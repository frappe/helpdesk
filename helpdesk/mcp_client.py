# Copyright (c) 2026, Quark Cyber Systems FZC and contributors
# For license information, please see license.txt

"""HTTP client for customer MCP endpoints."""

import json
import time
import uuid

import frappe
import requests
from frappe.utils.password import get_decrypted_password

MCP_TIMEOUT = 30  # seconds
MCP_RETRY_COUNT = 1

# Per-tool mapping of the argument key holding the row limit to the QCS Hub
# Settings field that caps it. Hub-enforced to protect the Anthropic token
# budget; applied in addition to (and independently of) the customer-site cap.
_TOOL_LIMIT_FIELD = {
	"get_list": ("limit", "hub_max_list_limit", 200),
	"get_error_log": ("limit", "hub_max_error_log_limit", 50),
	"execute_report": ("limit", "hub_max_report_rows", 500),
}


def _clamp_hub_limit(tool_name: str, arguments: dict) -> dict:
	"""Clamp the `limit` argument against the Hub's per-tool cap.

	Returns a shallow-copied arguments dict with the limit adjusted. Does
	nothing if the tool isn't in the cap map, or if the arguments don't
	contain a limit. Silently falls back to the default on any lookup error
	so a missing/misconfigured Hub Settings row doesn't break investigations.
	"""
	cap_spec = _TOOL_LIMIT_FIELD.get(tool_name)
	if not cap_spec:
		return arguments
	arg_key, settings_field, default = cap_spec
	if arg_key not in (arguments or {}):
		return arguments

	try:
		cap = frappe.db.get_single_value("HDS Hub Settings", settings_field)
		cap = int(cap) if cap and int(cap) > 0 else default
	except Exception:
		cap = default

	requested = int(arguments.get(arg_key) or 0)
	if requested <= 0 or requested > cap:
		arguments = dict(arguments)
		arguments[arg_key] = cap
	return arguments


class MCPClient:
	"""Client for calling MCP tools on a customer's Frappe site."""

	def __init__(self, connection_name: str):
		"""Initialize from a HDS Support Connection document.

		Args:
			connection_name: Name of the HDS Support Connection doc
		"""
		conn = frappe.get_doc("HDS Support Connection", connection_name)
		self.connection_name = connection_name
		self.endpoint = conn.mcp_endpoint
		self.customer_name = conn.customer_name
		self.site_url = conn.site_url

		# Get credentials
		self.api_key = conn.api_key
		self.api_secret = get_decrypted_password("HDS Support Connection", connection_name, "api_secret")

		if not self.api_key or not self.api_secret:
			frappe.throw(f"Missing API credentials for connection {connection_name}")

		# Session management
		self.session_id = None
		self._initialize()

	def _initialize(self):
		"""Perform MCP initialize handshake."""
		response = self._post(
			{
				"jsonrpc": "2.0",
				"id": str(uuid.uuid4()),
				"method": "initialize",
				"params": {
					"protocolVersion": "2025-11-25",
					"capabilities": {},
					"clientInfo": {"name": "qcs-support-hub", "version": "0.1.0"},
				},
			}
		)

		self.session_id = response.headers.get("Mcp-Session-Id")

		# Send initialized notification
		self._post(
			{
				"jsonrpc": "2.0",
				"method": "notifications/initialized",
			},
			expect_response=False,
		)

	def list_tools(self) -> list[dict]:
		"""Get available tools from the MCP server."""
		result = self.call_jsonrpc("tools/list")
		return result.get("tools", [])

	def call_tool(self, tool_name: str, arguments: dict, ticket_id=None, session_id=None) -> dict:
		"""Call an MCP tool and return the result. Logs every call to HDS Remote Audit Log.

		Args:
			tool_name: Name of the tool to call
			arguments: Tool arguments
			ticket_id: Optional ticket ID for logging
			session_id: Optional session name for audit log session_id field

		Returns:
			dict with content, isError, and _meta
		"""
		arguments = _clamp_hub_limit(tool_name, arguments)

		start = time.monotonic()
		result = None
		error_message = ""

		try:
			result = self.call_jsonrpc(
				"tools/call",
				{
					"name": tool_name,
					"arguments": arguments,
				},
			)
		except Exception as e:
			error_message = str(e)[:500]
			result = {
				"content": [{"type": "text", "text": "MCP error: %s" % error_message}],
				"isError": True,
			}
			raise
		finally:
			elapsed_ms = round((time.monotonic() - start) * 1000)
			if result is not None:
				if "_meta" not in result:
					result["_meta"] = {}
				result["_meta"]["client_elapsed_ms"] = elapsed_ms
			self._log_audit(tool_name, arguments, result, elapsed_ms, session_id, error_message)

		return result

	def _log_audit(self, tool_name, arguments, result, elapsed_ms, session_id, error_message):
		"""Write an entry to HDS Remote Audit Log."""
		import json as _json

		WRITE_TOOLS = {"set_value", "set_values", "create_doc", "delete_doc", "run_doc_method", "clear_cache"}

		try:
			content = ""
			if result and result.get("content"):
				content = result["content"][0].get("text", "")[:500]
			is_error = bool(result and result.get("isError"))

			frappe.get_doc(
				{
					"doctype": "HDS Remote Audit Log",
					"connection": self.connection_name,
					"timestamp": frappe.utils.now_datetime(),
					"tool_name": tool_name,
					"action_type": "Write" if tool_name in WRITE_TOOLS else "Read",
					"status": "Error" if (is_error or error_message) else "Success",
					"execution_time_ms": elapsed_ms,
					"session_id": str(session_id) if session_id else "",
					"arguments": _json.dumps(arguments, default=str)[:2000],
					"result_summary": content if not is_error else "",
					"error_message": error_message or (content if is_error else ""),
				}
			).insert(ignore_permissions=True)
			frappe.db.commit()
		except Exception:
			frappe.log_error("Failed to write remote audit log")

	def call_jsonrpc(self, method: str, params: dict | None = None) -> dict:
		"""Send a JSON-RPC request and return the result."""
		request = {
			"jsonrpc": "2.0",
			"id": str(uuid.uuid4()),
			"method": method,
		}
		if params:
			request["params"] = params

		response = self._post(request)
		body = response.json()

		if "error" in body:
			error = body["error"]
			frappe.throw(f"MCP error {error.get('code')}: {error.get('message')}")

		return body.get("result", {})

	def _post(self, payload: dict, expect_response: bool = True) -> requests.Response:
		"""Send HTTP POST to the MCP endpoint with retry."""
		headers = {
			"Content-Type": "application/json",
			"Authorization": f"Token {self.api_key}:{self.api_secret}",
		}

		if self.session_id:
			headers["Mcp-Session-Id"] = self.session_id

		last_error = None
		for attempt in range(MCP_RETRY_COUNT + 1):
			try:
				response = requests.post(
					self.endpoint,
					json=payload,
					headers=headers,
					timeout=MCP_TIMEOUT,
				)

				if not expect_response:
					return response

				if response.status_code == 401:
					frappe.throw(f"Authentication failed for {self.site_url}")

				response.raise_for_status()
				return response

			except requests.Timeout:
				last_error = f"MCP request timed out after {MCP_TIMEOUT}s"
				if attempt < MCP_RETRY_COUNT:
					continue
			except requests.ConnectionError as e:
				last_error = f"Cannot connect to {self.site_url}: {e}"
				break
			except requests.HTTPError as e:
				last_error = f"HTTP error from {self.site_url}: {e}"
				break

		frappe.throw(last_error)

	def health_check(self) -> bool:
		"""Check if the MCP endpoint is reachable."""
		try:
			tools = self.list_tools()
			return len(tools) > 0
		except Exception:
			return False
