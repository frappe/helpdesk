# Copyright (c) 2026, Quark Cyber Systems FZC and contributors
# For license information, please see license.txt

"""Pull Pending Support Tickets from customer sites over MCP and turn them
into HD Tickets.

The customer site holds no credentials. Every call originates here, using
the per-connection API key stored on the Hub's HDS Support Connection —
the only place a credential belongs.
"""

import json

import frappe
import requests

from helpdesk.mcp_client import MCPClient

PULL_LIMIT = 20
RECORDING_TIMEOUT = 60
MAX_RECORDING_BYTES = 100 * 1024 * 1024


def _unwrap(result: dict):
	"""MCP tool results arrive as {"content": [{"type": "text", "text": "<json>"}]}."""
	if not result or result.get("isError"):
		raise ValueError("MCP call failed: %s" % result)

	for block in result.get("content", []):
		if block.get("type") == "text":
			return json.loads(block["text"])

	return None


def _pending_tickets(mcp: MCPClient) -> list[dict]:
	"""Fetch tickets the customer has raised but we have not imported."""
	result = mcp.call_tool(
		"get_list",
		{
			"doctype": "Support Ticket",
			"filters": {"status": "Pending"},
			"fields": [
				"name",
				"subject",
				"description",
				"raised_by",
				"screen_recording",
				"creation",
			],
			"limit": PULL_LIMIT,
		},
	)
	return _unwrap(result) or []


def _ticket_files(mcp: MCPClient, ticket_name: str) -> list[dict]:
	"""All files the customer attached to the ticket (recording, screenshots).

	Falls back to an empty list if the customer blocks the File doctype in
	their MCP access control — the ticket still imports, just without media.
	"""
	try:
		result = mcp.call_tool(
			"get_list",
			{
				"doctype": "File",
				"filters": {
					"attached_to_doctype": "Support Ticket",
					"attached_to_name": ticket_name,
				},
				"fields": ["file_url", "file_name"],
				"limit": 20,
			},
		)
		return _unwrap(result) or []
	except Exception:
		frappe.log_error(
			title=f"File listing failed for {ticket_name}",
			message=frappe.get_traceback(),
		)
		return []


def _already_imported(connection_name: str, client_ticket: str) -> bool:
	"""Guard against re-importing when a previous push-back failed.

	If we created the HD Ticket but could not write the status back, the
	client ticket stays Pending and we would otherwise import it again on
	the next cycle.
	"""
	return bool(
		frappe.db.exists(
			"HD Ticket",
			{
				"custom_qcs_connection": connection_name,
				"custom_client_ticket": client_ticket,
			},
		)
	)


def _create_hd_ticket(connection_name: str, customer: str, ticket: dict) -> str:
	"""Create the Helpdesk ticket for a pulled customer request.

	AI triage fires automatically from the HD Ticket after_insert hook
	(see hooks.py doc_events) — do not enqueue it again here.
	"""
	hd = frappe.get_doc({
		"doctype": "HD Ticket",
		"subject": ticket.get("subject") or "Support request",
		"description": ticket.get("description") or "",
		"customer": customer,
		"raised_by": ticket.get("raised_by"),
		"via_customer_portal": 1,
	}).insert(ignore_permissions=True)

	frappe.db.set_value(
		"HD Ticket",
		hd.name,
		{
			"custom_qcs_connection": connection_name,
			"custom_client_ticket": ticket.get("name"),
		},
		update_modified=False,
	)

	return hd.name


def _attach_recording(mcp: MCPClient, hd_ticket_name: str, file_url: str | None) -> str | None:
	"""Download the customer's screen recording and attach it to the HD Ticket.

	The recording is a private File on the customer's site. We already hold
	that site's API key on the connection, so this is a plain authenticated
	GET — no new MCP tool required, and nothing is uploaded by the client.
	"""
	if not file_url:
		return None

	response = requests.get(
		f"{mcp.site_url.rstrip('/')}{file_url}",
		headers={"Authorization": f"token {mcp.api_key}:{mcp.api_secret}"},
		timeout=RECORDING_TIMEOUT,
		stream=True,
	)
	response.raise_for_status()

	content = response.raw.read(MAX_RECORDING_BYTES + 1, decode_content=True)
	if len(content) > MAX_RECORDING_BYTES:
		frappe.log_error(
			title=f"Recording too large for {hd_ticket_name}",
			message=f"{file_url} exceeded {MAX_RECORDING_BYTES} bytes; not attached",
		)
		return None

	file_doc = frappe.get_doc({
		"doctype": "File",
		"file_name": file_url.rsplit("/", 1)[-1],
		"attached_to_doctype": "HD Ticket",
		"attached_to_name": hd_ticket_name,
		"is_private": 1,
		"content": content,
	}).insert(ignore_permissions=True)

	# Surface the file inside the Helpdesk agent UI. The agent portal renders
	# its own HD Ticket Comment doctype — a core frappe Comment only shows in
	# the desk view, which agents never open.
	is_video = file_doc.file_name.rsplit(".", 1)[-1].lower() in ("webm", "mp4", "mov", "mkv")
	label = "Screen recording" if is_video else "Screenshot"
	icon = "\N{VIDEO CAMERA}" if is_video else "\N{FRAME WITH PICTURE}"
	comment = frappe.get_doc({
		"doctype": "HD Ticket Comment",
		"reference_ticket": hd_ticket_name,
		"commented_by": "Administrator",
		"content": (
			f'{icon} {label} from the customer: '
			f'<a href="{file_doc.file_url}" target="_blank">{file_doc.file_name}</a>'
		),
	})
	comment.flags.skip_notifications = True
	comment.insert(ignore_permissions=True)

	return file_doc.name


def _push_back(mcp: MCPClient, client_ticket: str, values: dict) -> None:
	"""Write status/ID/triage back onto the customer's local Support Ticket."""
	mcp.call_tool(
		"set_values",
		{
			"doctype": "Support Ticket",
			"name": client_ticket,
			"values": values,
		},
	)


def pull_client_tickets() -> int:
	"""Scheduled: turn Pending client tickets into HD Tickets."""
	connections = frappe.get_all(
		"HDS Support Connection",
		filters={"connection_status": "Connected"},
		fields=["name", "customer_name"],
	)

	created = 0
	for conn in connections:
		try:
			mcp = MCPClient(conn.name)
			tickets = _pending_tickets(mcp)
		except Exception:
			frappe.log_error(
				title=f"Ticket pull failed for {conn.name}",
				message=frappe.get_traceback(),
			)
			continue

		for ticket in tickets:
			try:
				if _already_imported(conn.name, ticket["name"]):
					# HD Ticket exists; the previous push-back must have failed.
					_push_back(mcp, ticket["name"], {"status": "Open"})
					continue

				hd_name = _create_hd_ticket(conn.name, conn.customer_name, ticket)

				# Media is nice-to-have; never let a fetch failure (403,
				# timeout, ...) block the ticket import — that would retry
				# the same ticket every cycle forever.
				files = _ticket_files(mcp, ticket["name"])
				if not files and ticket.get("screen_recording"):
					# older clients that don't attach files to the ticket
					files = [{"file_url": ticket["screen_recording"]}]
				for f in files:
					try:
						_attach_recording(mcp, hd_name, f.get("file_url"))
					except Exception:
						frappe.log_error(
							title=f"Media attach failed for {ticket.get('name')}",
							message=frappe.get_traceback(),
						)
				frappe.db.commit()

				_push_back(mcp, ticket["name"], {"ticket_id": hd_name, "status": "Open"})
				created += 1
			except Exception:
				frappe.db.rollback()
				frappe.log_error(
					title=f"Ticket import failed for {ticket.get('name')}",
					message=frappe.get_traceback(),
				)

	return created


def push_ticket_statuses() -> int:
	"""Scheduled: mirror HD Ticket status onto the customer's local tickets."""
	rows = frappe.get_all(
		"HD Ticket",
		filters={
			"custom_client_ticket": ["is", "set"],
			"custom_qcs_connection": ["is", "set"],
		},
		fields=[
			"name",
			"status",
			"priority",
			"custom_client_ticket",
			"custom_qcs_connection",
		],
		limit=200,
	)

	by_connection = {}
	for row in rows:
		by_connection.setdefault(row.custom_qcs_connection, []).append(row)

	pushed = 0
	for connection_name, tickets in by_connection.items():
		try:
			mcp = MCPClient(connection_name)
		except Exception:
			frappe.log_error(
				title=f"Status push failed for {connection_name}",
				message=frappe.get_traceback(),
			)
			continue

		for row in tickets:
			try:
				_push_back(
					mcp,
					row.custom_client_ticket,
					{"status": row.status, "priority": row.priority or ""},
				)
				pushed += 1
			except Exception:
				frappe.log_error(
					title=f"Status push failed for {row.name}",
					message=frappe.get_traceback(),
				)

	return pushed


def sync_conversations() -> int:
	"""Scheduled: two-way conversation + client close requests, per linked ticket.

	- Client comments (not authored by the support user) become HD Ticket
	  Comments so agents see the customer's replies.
	- Agent replies (Sent Communications on the HD Ticket) are pushed to the
	  client as support-user comments; the client notifies the reporter.
	- close_requested on the client closes the HD Ticket; the status push
	  mirrors Closed back, confirming to the user.

	Idempotency: synced record names are tracked in custom_conv_state.
	"""
	rows = frappe.get_all(
		"HD Ticket",
		filters={"custom_client_ticket": ["is", "set"], "custom_qcs_connection": ["is", "set"],
		         "status": ["!=", "Closed"]},
		fields=["name", "custom_client_ticket", "custom_qcs_connection", "custom_conv_state"],
		limit=100,
	)
	by_conn = {}
	for r in rows:
		by_conn.setdefault(r.custom_qcs_connection, []).append(r)

	synced = 0
	for conn_name, tickets in by_conn.items():
		try:
			mcp = MCPClient(conn_name)
		except Exception:
			frappe.log_error(title=f"Conversation sync failed for {conn_name}",
			                 message=frappe.get_traceback())
			continue

		for row in tickets:
			try:
				state = json.loads(row.custom_conv_state or "{}")
				state.setdefault("client", [])
				state.setdefault("hub", [])
				ct = row.custom_client_ticket

				# client -> hub: customer comments
				comments = _unwrap(mcp.call_tool("get_list", {
					"doctype": "Comment",
					"filters": {"reference_doctype": "Support Ticket",
					            "reference_name": ct, "comment_type": "Comment"},
					"fields": ["name", "content", "owner"],
					"limit": 50,
				})) or []
				for c in comments:
					if c["name"] in state["client"] or c.get("owner") == "support@quarkcs.com":
						continue
					hd_comment = frappe.get_doc({
						"doctype": "HD Ticket Comment", "reference_ticket": row.name,
						"commented_by": "Administrator",
						"content": "\N{SPEECH BALLOON} Customer (%s): %s" % (c.get("owner"), c.get("content") or ""),
					})
					hd_comment.flags.skip_notifications = True
					hd_comment.insert(ignore_permissions=True)
					state["client"].append(c["name"])
					synced += 1

				# hub -> client: agent replies (sent communications)
				replies = frappe.get_all(
					"Communication",
					filters={"reference_doctype": "HD Ticket", "reference_name": row.name,
					         "communication_type": "Communication", "sent_or_received": "Sent"},
					fields=["name", "content"],
					limit=50,
				)
				for m in replies:
					if m.name in state["hub"]:
						continue
					mcp.call_tool("create_doc", {
						"doctype": "Comment",
						"values": {"comment_type": "Comment",
						           "reference_doctype": "Support Ticket",
						           "reference_name": ct, "content": m.content or ""},
					})
					state["hub"].append(m.name)
					synced += 1

				# new files attached to the client ticket after import
				# (e.g. a follow-up recording or screenshot on a reply)
				state.setdefault("files", [])
				for f in _ticket_files(mcp, ct):
					url = f.get("file_url")
					if not url or url in state["files"]:
						continue
					fname = url.rsplit("/", 1)[-1]
					if frappe.db.exists("File", {
						"attached_to_doctype": "HD Ticket",
						"attached_to_name": row.name,
						"file_name": fname,
					}):
						state["files"].append(url)  # imported at creation
						continue
					_attach_recording(mcp, row.name, url)
					state["files"].append(url)
					synced += 1

				# client close request?
				req = _unwrap(mcp.call_tool("get_list", {
					"doctype": "Support Ticket",
					"filters": {"name": ct, "close_requested": 1},
					"fields": ["name"], "limit": 1,
				})) or []
				if req:
					frappe.db.set_value("HD Ticket", row.name, "status", "Closed")

				frappe.db.set_value("HD Ticket", row.name, "custom_conv_state",
				                    json.dumps(state), update_modified=False)
				frappe.db.commit()
			except Exception:
				frappe.db.rollback()
				frappe.log_error(title=f"Conversation sync failed for {row.name}",
				                 message=frappe.get_traceback())
	return synced

