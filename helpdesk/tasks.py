# Copyright (c) 2026, Quark Cyber Systems FZC and contributors
# For license information, please see license.txt

"""Scheduled jobs for QCS Support Hub."""

import frappe
from frappe.utils import now_datetime

from helpdesk.mcp_client import MCPClient


def health_check_connections():
	"""Daily: ping each customer MCP endpoint and update connection status."""
	connections = frappe.get_all(
		"HDS Support Connection",
		filters={"connection_status": ["in", ["Connected", "Disconnected", "Error"]]},
		fields=["name", "site_url", "customer_name"],
	)

	for conn in connections:
		try:
			mcp = MCPClient(conn.name)
			is_healthy = mcp.health_check()

			frappe.db.set_value(
				"HDS Support Connection",
				conn.name,
				{
					"connection_status": "Connected" if is_healthy else "Error",
					"last_health_check": now_datetime(),
					"last_error": "" if is_healthy else "Health check failed: no tools returned",
				},
				update_modified=False,
			)

		except Exception as e:
			frappe.db.set_value(
				"HDS Support Connection",
				conn.name,
				{
					"connection_status": "Error",
					"last_health_check": now_datetime(),
					"last_error": str(e)[:200],
				},
				update_modified=False,
			)

	frappe.db.commit()


def retry_pending_triages():
	"""Daily: re-enqueue failed/pending triages within retry limit."""
	tickets = frappe.get_all(
		"HD Ticket",
		filters={
			"custom_triage_status": ["in", ["Pending", "Failed"]],
			"status": ["!=", "Closed"],
		},
		fields=["name"],
		limit=20,
	)

	for ticket in tickets:
		try:
			from helpdesk.triage import run_triage_now

			run_triage_now(str(ticket.name))
		except Exception:
			pass  # run_triage_now handles its own errors


def sync_model_pricing():
	"""Weekly: flag HDS Model Pricing rows that have not been reviewed in >90 days.

	Anthropic does not publish a machine-readable price list, so this job does not
	fetch prices automatically. It logs stale rows so an admin can review them
	against https://platform.claude.com/docs/en/about-claude/models/overview .
	"""
	from frappe.utils import add_days

	cutoff = add_days(now_datetime(), -90)
	stale = frappe.get_all(
		"HDS Model Pricing",
		filters={"is_active": 1, "last_synced_on": ["<", cutoff]},
		fields=["name", "last_synced_on"],
	)

	if not stale:
		return

	names = ", ".join(r.name for r in stale)
	frappe.log_error(
		title="HDS Model Pricing review due",
		message=(
			f"{len(stale)} active model(s) have not had pricing reviewed in 90+ days: "
			f"{names}. Verify against provider pricing page and update "
			f"'Last Synced On' on each row."
		),
	)


def pull_client_tickets():
	"""Every 5 min: import Pending tickets from customer sites over MCP."""
	from helpdesk.ticket_puller import pull_client_tickets as _pull

	return _pull()


def push_ticket_statuses():
	"""Every 5 min: mirror HD Ticket status back onto customer sites."""
	from helpdesk.ticket_puller import push_ticket_statuses as _push

	return _push()


def sync_conversations():
	"""Every 5 min: two-way comments + client close requests over MCP."""
	from helpdesk.ticket_puller import sync_conversations as _sync

	return _sync()

