# Copyright (c) 2026, Quark Cyber Systems FZC and contributors
# For license information, please see license.txt

"""Write operation approval workflow.

When Sonnet proposes write operations during an investigation, they are
captured as HDS Support Action Requests with individual proposed actions.
An agent reviews and approves/rejects each action, then the Hub executes
the approved ones via MCP.
"""

import json

import frappe
from frappe.utils import now_datetime

from helpdesk.mcp_client import MCPClient

# Risk levels for write operations
RISK_LEVELS = {
	"clear_cache": "Low",
	"set_value": "Medium",
	"set_values": "Medium",
	"create_doc": "Medium",
	"run_doc_method": "High",
	"delete_doc": "High",
}


def create_action_request(session_name, ticket_id, proposed_actions):
	"""Create an action request from AI-proposed write operations.

	Args:
		session_name: HDS AI Support Session name
		ticket_id: HD Ticket name
		proposed_actions: list of dicts with tool_name, description, arguments

	Returns:
		HDS Support Action Request name
	"""
	session = frappe.get_doc("HDS AI Support Session", session_name)

	action_request = frappe.get_doc(
		{
			"doctype": "HDS Support Action Request",
			"ticket": ticket_id,
			"session": session_name,
			"customer_name": session.customer_name,
			"site_url": frappe.db.get_value("HDS Support Connection", session.connection, "site_url")
			if session.connection
			else "",
			"status": "Pending Approval",
			"diagnosis": session.diagnosis or "",
		}
	)

	for action in proposed_actions:
		action_request.append(
			"proposed_actions",
			{
				"tool_name": action.get("tool_name"),
				"description": action.get("description", ""),
				"arguments": json.dumps(action.get("arguments", {}), default=str),
				"risk_level": RISK_LEVELS.get(action.get("tool_name"), "Medium"),
				"approved": 0,
			},
		)

	action_request.insert(ignore_permissions=True)
	frappe.db.commit()
	return action_request.name


def approve_actions(action_request_name, approved_indices=None):
	"""Approve specific actions in an action request.

	Args:
		action_request_name: HDS Support Action Request name
		approved_indices: list of row indices to approve (0-based). If None, approve all.
	"""
	ar = frappe.get_doc("HDS Support Action Request", action_request_name)

	if ar.status not in ("Pending Approval",):
		frappe.throw("Action request is not pending approval")

	for i, action in enumerate(ar.proposed_actions):
		if approved_indices is None or i in approved_indices:
			action.approved = 1

	has_approved = any(a.approved for a in ar.proposed_actions)
	all_approved = all(a.approved for a in ar.proposed_actions)

	if all_approved:
		ar.status = "Approved"
	elif has_approved:
		ar.status = "Partially Approved"
	else:
		ar.status = "Rejected"

	ar.approved_by = frappe.session.user
	ar.approved_at = now_datetime()
	ar.save(ignore_permissions=True)
	frappe.db.commit()

	return ar.status


def reject_actions(action_request_name):
	"""Reject all actions in an action request."""
	ar = frappe.get_doc("HDS Support Action Request", action_request_name)

	if ar.status not in ("Pending Approval",):
		frappe.throw("Action request is not pending approval")

	ar.status = "Rejected"
	ar.approved_by = frappe.session.user
	ar.approved_at = now_datetime()
	ar.save(ignore_permissions=True)
	frappe.db.commit()

	return "Rejected"


def execute_approved_actions(action_request_name):
	"""Execute all approved actions via MCP.

	Args:
		action_request_name: HDS Support Action Request name

	Returns:
		dict with results per action
	"""
	ar = frappe.get_doc("HDS Support Action Request", action_request_name)

	if ar.status not in ("Approved", "Partially Approved"):
		frappe.throw("Action request is not approved")

	# Get connection from the session
	session = frappe.get_doc("HDS AI Support Session", ar.session)
	if not session.connection:
		frappe.throw("No connection found for this session")

	mcp = MCPClient(session.connection)

	execution_log = []
	all_success = True

	for action in ar.proposed_actions:
		if not action.approved:
			action.execution_result = "Skipped (not approved)"
			continue

		try:
			arguments = json.loads(action.arguments) if action.arguments else {}
			result = mcp.call_tool(action.tool_name, arguments)

			content = ""
			if result.get("content"):
				content = result["content"][0].get("text", "")

			if result.get("isError"):
				action.execution_result = "Error: " + content[:200]
				all_success = False
				execution_log.append("FAILED: %s - %s" % (action.tool_name, content[:200]))
			else:
				action.execution_result = "Success: " + content[:200]
				execution_log.append("OK: %s - %s" % (action.tool_name, content[:100]))

		except Exception as e:
			action.execution_result = "Exception: " + str(e)[:200]
			all_success = False
			execution_log.append("EXCEPTION: %s - %s" % (action.tool_name, str(e)[:200]))

	ar.status = "Executed" if all_success else "Failed"
	ar.executed_at = now_datetime()
	ar.execution_log = "\n".join(execution_log)
	ar.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"status": ar.status,
		"results": execution_log,
	}
