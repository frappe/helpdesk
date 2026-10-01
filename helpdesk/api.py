# Copyright (c) 2026, Quark Cyber Systems FZC and contributors
# For license information, please see license.txt

"""Whitelisted API endpoints for HD Form Script and external calls."""

import json

import frappe


@frappe.whitelist()
def get_triage(ticket):
	"""Get triage results for a ticket."""
	ticket = str(ticket)
	ticket_doc = frappe.get_doc("HD Ticket", ticket)
	triage_data = json.loads(ticket_doc.custom_triage_data or "{}") if ticket_doc.custom_triage_data else {}

	return {
		"status": ticket_doc.custom_triage_status or "",
		"category": ticket_doc.custom_triage_category or "",
		"priority": ticket_doc.custom_triage_priority or "",
		"complexity": ticket_doc.custom_triage_complexity or "",
		"summary": ticket_doc.custom_triage_summary or "",
		"recommended_track": ticket_doc.custom_triage_recommended_track or "",
		"timestamp": str(ticket_doc.custom_triage_timestamp) if ticket_doc.custom_triage_timestamp else "",
		"data": triage_data,
	}


@frappe.whitelist()
def run_triage_now(ticket):
	"""Manually trigger triage for a ticket."""
	from helpdesk.triage import run_triage_now as _run_triage_now

	return _run_triage_now(str(ticket))


@frappe.whitelist()
def start_investigation(ticket, connection, agent_notes=""):
	"""Start an AI investigation session."""
	from helpdesk.session_manager import start_investigation as _start

	session_name = _start(str(ticket), str(connection), agent_notes)
	return {"session": session_name, "status": "started"}


@frappe.whitelist()
def get_sessions(ticket):
	"""Get all investigation sessions for a ticket."""
	ticket = str(ticket)
	sessions = frappe.get_list(
		"HDS AI Support Session",
		filters={"ticket": ticket},
		fields=[
			"name",
			"status",
			"started_at",
			"ended_at",
			"total_tool_calls",
			"estimated_cost_usd",
			"model_used",
			"customer_name",
			"diagnosis",
		],
		order_by="creation desc",
	)
	return sessions


@frappe.whitelist()
def get_session_detail(session):
	"""Get full session details including MCP call logs."""
	doc = frappe.get_doc("HDS AI Support Session", session)
	return doc.as_dict()


@frappe.whitelist()
def resume_session(session, agent_guidance=""):
	"""Resume a paused (Awaiting Review) session with optional agent guidance."""
	from helpdesk.session_manager import resume_investigation

	session_name = resume_investigation(str(session), agent_guidance or "")
	return {"session": session_name, "status": "resumed"}


@frappe.whitelist()
def cancel_session(session):
	"""Cancel a paused session permanently."""
	doc = frappe.get_doc("HDS AI Support Session", str(session))
	if doc.status not in ("Awaiting Review", "Active"):
		frappe.throw("Cannot cancel a session in status '%s'" % doc.status)
	doc.status = "Cancelled"
	doc.ended_at = frappe.utils.now_datetime()
	doc.conversation_state = ""
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"status": "cancelled"}


@frappe.whitelist()
def get_pending_actions(ticket):
	"""Get pending action requests for a ticket."""
	ticket = str(ticket)
	return frappe.get_list(
		"HDS Support Action Request",
		filters={"ticket": ticket, "status": "Pending Approval"},
		fields=["name", "status", "diagnosis", "session"],
		order_by="creation desc",
	)


@frappe.whitelist()
def get_connections():
	"""Get all support connections."""
	return frappe.get_list(
		"HDS Support Connection",
		fields=["name", "customer_name", "site_url", "connection_status"],
		order_by="customer_name asc",
	)


@frappe.whitelist()
def get_login_url(connection, ticket=None):
	"""Get a one-time login URL for a customer site.

	Calls the customer's generate_login_url API via MCP credentials.
	Logs every attempt (success or failure) to HDS Site Login Log.

	Auth gate: caller must be logged in and have read on QCS Support
	Connection (Agent or System Manager). User Permission filtering on
	the customer_name Link is bypassed here so agents are not blocked
	from sites whose HD Customer they aren't directly permissioned for -
	the action is audit-logged so misuse is traceable.
	"""
	import requests
	from frappe.utils.password import get_decrypted_password

	connection = str(connection)
	conn = frappe.get_doc("HDS Support Connection", connection)

	if not conn.api_key or not conn.site_url:
		_log_login_attempt(connection, ticket, "Failed", "Connection not configured")
		frappe.throw("Connection not configured")

	api_secret = get_decrypted_password("HDS Support Connection", connection, "api_secret")
	if not api_secret:
		_log_login_attempt(connection, ticket, "Failed", "API secret not found")
		frappe.throw("API secret not found for connection")

	url = f"{conn.site_url}/api/method/qcs_support_client.api.generate_login_url"

	try:
		response = requests.post(
			url,
			headers={"Authorization": "Token %s:%s" % (conn.api_key, api_secret)},
			timeout=15,
		)
		if response.status_code != 200:
			_log_login_attempt(
				connection, ticket, "Failed", "HTTP %d: %s" % (response.status_code, response.text[:150])
			)
			frappe.throw("Failed to generate login URL: %s" % response.text[:200])

		data = response.json().get("message", {})
		login_url = data.get("login_url")

		# Structured audit log
		_log_login_attempt(connection, ticket, "Success", "")

		return {"login_url": login_url, "site_url": conn.site_url}

	except requests.Timeout:
		_log_login_attempt(connection, ticket, "Failed", "Timeout")
		frappe.throw("Customer site unreachable (timeout)")
	except requests.ConnectionError as e:
		_log_login_attempt(connection, ticket, "Failed", "Connection error: %s" % str(e)[:100])
		frappe.throw("Cannot connect to customer site: %s" % str(e)[:100])


def _log_login_attempt(connection, ticket, status, error_message, event_type="Login"):
	"""Insert a HDS Site Login Log entry."""
	try:
		frappe.get_doc(
			{
				"doctype": "HDS Site Login Log",
				"agent": frappe.session.user,
				"connection": connection,
				"ticket": str(ticket) if ticket else None,
				"status": status,
				"event_type": event_type,
				"error_message": error_message or "",
			}
		).insert(ignore_permissions=True)
		frappe.db.commit()
	except Exception:
		frappe.log_error("Failed to write login log")


@frappe.whitelist()
def get_remote_audit_log(connection, action_type=None, tool_name=None, status=None, limit=100):
	"""Return audit log entries for a connection.

	Entries are written directly by the Hub after every MCP call (see mcp_client._log_audit).
	"""
	connection = str(connection)
	filters = {"connection": connection}
	if action_type:
		filters["action_type"] = action_type
	if tool_name:
		filters["tool_name"] = tool_name
	if status:
		filters["status"] = status

	entries = frappe.get_list(
		"HDS Remote Audit Log",
		filters=filters,
		fields=[
			"name",
			"timestamp",
			"tool_name",
			"action_type",
			"status",
			"arguments",
			"result_summary",
			"error_message",
			"execution_time_ms",
			"session_id",
		],
		order_by="timestamp desc",
		limit_page_length=int(limit),
	)

	return {"entries": entries}


@frappe.whitelist()
def view_connection_credentials(connection):
	"""Return decrypted credentials + ready-to-paste client configs.

	System Manager only. Every access is audit-logged.
	"""
	if "System Manager" not in frappe.get_roles(frappe.session.user):
		_log_login_attempt(connection, None, "Failed", "Not a System Manager", event_type="Credential View")
		frappe.throw("Only System Managers can view credentials", frappe.PermissionError)

	from frappe.utils.password import get_decrypted_password

	connection = str(connection)
	conn = frappe.get_doc("HDS Support Connection", connection)

	if not conn.api_key:
		_log_login_attempt(
			connection, None, "Failed", "No API key on connection", event_type="Credential View"
		)
		frappe.throw("No API key set on this connection")

	api_secret = get_decrypted_password(
		"HDS Support Connection", connection, "api_secret", raise_exception=False
	)
	if not api_secret:
		_log_login_attempt(
			connection, None, "Failed", "No API secret on connection", event_type="Credential View"
		)
		frappe.throw("No API secret set on this connection")

	# Build a Claude Desktop config snippet
	mcp_url = f"{conn.site_url}/api/method/qcs_support_client.mcp.handler.handle"

	slug = (conn.customer_name or conn.name).lower().replace(" ", "-").replace(".", "-")
	desktop_args = [
		"C:\\\\Users\\\\<YOUR_USER>\\\\AppData\\\\Roaming\\\\npm\\\\node_modules\\\\mcp-remote\\\\dist\\\\proxy.js",
		mcp_url,
		"--header",
		"Authorization: Token %s:%s" % (conn.api_key, api_secret),
	]
	if conn.site_url.startswith("http://"):
		desktop_args.append("--allow-http")

	import json

	desktop_config = json.dumps(
		{
			"mcpServers": {
				slug: {
					"command": "node",
					"args": desktop_args,
				}
			}
		},
		indent=2,
	)

	# Audit log BEFORE returning credentials
	_log_login_attempt(connection, None, "Success", "", event_type="Credential View")

	return {
		"api_key": conn.api_key,
		"api_secret": api_secret,
		"token": "%s:%s" % (conn.api_key, api_secret),
		"site_url": conn.site_url,
		"mcp_url": mcp_url,
		"desktop_config": desktop_config,
	}


@frappe.whitelist()
def get_action_request_detail(action_request):
	"""Get full action request details including proposed actions."""
	doc = frappe.get_doc("HDS Support Action Request", str(action_request))
	return doc.as_dict()


@frappe.whitelist()
def approve_and_execute(action_request, approved_indices=None, execute=True):
	"""Approve actions and optionally execute them.

	Args:
		action_request: HDS Support Action Request name
		approved_indices: JSON list of indices to approve (0-based). None = approve all.
		execute: Whether to execute immediately after approval
	"""
	from helpdesk.approval import approve_actions, execute_approved_actions

	action_request = str(action_request)

	if approved_indices and isinstance(approved_indices, str):
		import json

		approved_indices = json.loads(approved_indices)

	status = approve_actions(action_request, approved_indices)

	result = {"approval_status": status}

	if execute and status in ("Approved", "Partially Approved"):
		exec_result = execute_approved_actions(action_request)
		result["execution"] = exec_result

	return result


@frappe.whitelist()
def reject_action_request(action_request):
	"""Reject all actions in an action request."""
	from helpdesk.approval import reject_actions

	return {"status": reject_actions(str(action_request))}


def _call_client(conn, connection_name, path: str, payload: dict | None = None) -> dict:
	"""Helper: POST to a customer site endpoint with Token auth from the Connection."""
	import requests
	from frappe.utils.password import get_decrypted_password

	if not conn.api_key:
		frappe.throw("API Key is missing on this connection.")
	api_secret = get_decrypted_password(
		"HDS Support Connection", connection_name, "api_secret", raise_exception=False
	)
	if not api_secret:
		frappe.throw("API Secret is missing on this connection.")

	url = f"{conn.site_url}{path}"
	try:
		response = requests.post(
			url,
			headers={"Authorization": f"Token {conn.api_key}:{api_secret}"},
			json=payload or {},
			timeout=30,
		)
	except requests.Timeout:
		frappe.throw(f"Customer site unreachable (timeout): {conn.site_url}")
	except requests.ConnectionError as e:
		frappe.throw(f"Cannot connect to {conn.site_url}: {str(e)[:150]}")

	if response.status_code == 401:
		frappe.throw(
			f"Authentication failed on {conn.site_url}. "
			"Verify API Key/Secret belong to support@quarkcs.com on the customer site."
		)
	if response.status_code != 200:
		frappe.throw(f"Customer site refused request: {response.text[:400]}")
	return response.json().get("message", {})


@frappe.whitelist()
def register_client(connection: str):
	"""Hub-initiated connection handshake.

	Prerequisites (one-time, manual):
	  - Customer admin has installed qcs_support_client, configured QCS Support
	    Settings (Hub URL, enabled), and generated API keys for
	    support@quarkcs.com via the User doc -> API Access.
	  - Hub admin has pasted those api_key/api_secret into this Connection.

	This call uses Token auth (api_key:api_secret) against the customer site.
	It records the Hub URL + client_id on the customer side and marks this
	Connection as Connected on the Hub side. No secrets are exchanged.
	"""
	from frappe.utils import get_url

	conn = frappe.get_doc("HDS Support Connection", connection)

	if not conn.site_url:
		_log_login_attempt(connection, None, "Failed", "Site URL missing", event_type="Register")
		frappe.throw("Site URL is required on the connection")

	try:
		result = _call_client(
			conn,
			connection,
			"/api/method/qcs_support_client.api.register_connection",
			{"hub_url": get_url(), "client_id": connection},
		)
	except Exception as e:
		_log_login_attempt(connection, None, "Failed", str(e)[:200], event_type="Register")
		raise

	conn.connection_status = "Connected"
	conn.mcp_client_installed = 1
	conn.last_token_update = frappe.utils.now_datetime()
	conn.save(ignore_permissions=True)
	frappe.db.commit()

	_log_login_attempt(connection, None, "Success", "", event_type="Register")

	return {"status": "registered", "connection": connection, "site": result.get("site")}


@frappe.whitelist()
def rotate_credentials(connection: str):
	"""Hub-initiated credential rotation.

	The Hub generates a new api_key + api_secret, calls the customer site
	with the CURRENT credentials (Token auth), and on success swaps its
	stored credentials to the new ones.
	"""
	conn = frappe.get_doc("HDS Support Connection", connection)
	if not conn.site_url:
		_log_login_attempt(connection, None, "Failed", "Site URL missing", event_type="Rotate Credentials")
		frappe.throw("Site URL is required")

	new_api_key = frappe.generate_hash(length=15)
	new_api_secret = frappe.generate_hash(length=15)

	try:
		# Call customer site with CURRENT credentials (before swapping).
		_call_client(
			conn,
			connection,
			"/api/method/qcs_support_client.api.rotate_credentials",
			{"new_api_key": new_api_key, "new_api_secret": new_api_secret},
		)
	except Exception as e:
		_log_login_attempt(connection, None, "Failed", str(e)[:200], event_type="Rotate Credentials")
		raise

	# Swap stored credentials. save() encrypts the Password field.
	conn.api_key = new_api_key
	conn.api_secret = new_api_secret
	conn.last_token_update = frappe.utils.now_datetime()
	conn.save(ignore_permissions=True)
	frappe.db.commit()

	_log_login_attempt(connection, None, "Success", "", event_type="Rotate Credentials")

	return {"status": "rotated", "connection": connection}


@frappe.whitelist()
def deregister_client(connection: str):
	"""Hub-initiated deregistration.

	Calls the customer site (Token auth) to clear its client_id/contract_active,
	then marks this Connection as Disconnected. Does NOT revoke the api_key on
	the customer site - the customer admin controls that via User -> API Access.
	"""
	conn = frappe.get_doc("HDS Support Connection", connection)
	if not conn.site_url:
		_log_login_attempt(connection, None, "Failed", "Site URL missing", event_type="Deregister")
		frappe.throw("Site URL is required")

	try:
		_call_client(
			conn,
			connection,
			"/api/method/qcs_support_client.api.deregister",
			{},
		)
	except Exception as e:
		_log_login_attempt(connection, None, "Failed", str(e)[:200], event_type="Deregister")
		raise

	conn.connection_status = "Disconnected"
	conn.save(ignore_permissions=True)
	frappe.db.commit()

	_log_login_attempt(connection, None, "Success", "", event_type="Deregister")

	return {"status": "deregistered", "connection": connection}
