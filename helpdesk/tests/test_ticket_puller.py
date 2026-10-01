# Copyright (c) 2026, Quark Cyber Systems FZC and contributors
# For license information, please see license.txt

"""Tests for the zero-client-key ticket flow.

Run on the staging hub (Frappe v16 + Helpdesk + helpdesk):
    bench --site <staging-hub> run-tests --module helpdesk.tests.test_ticket_puller
"""

import json
from unittest.mock import MagicMock

import frappe
from frappe.tests.utils import FrappeTestCase


def mcp_result(payload):
	"""Shape an MCP tools/call result the way MCPClient returns it."""
	return {"content": [{"type": "text", "text": json.dumps(payload)}], "isError": False}


class TestPendingTickets(FrappeTestCase):
	def test_parses_mcp_payload(self):
		from helpdesk.ticket_puller import _pending_tickets

		mcp = MagicMock()
		mcp.call_tool.return_value = mcp_result([
			{
				"name": "SUP-2026-00001",
				"subject": "Printer offline",
				"description": "<p>offline</p>",
				"raised_by": "user@avientek.com",
				"screen_recording": "/private/files/rec.mp4",
			},
		])

		tickets = _pending_tickets(mcp)

		self.assertEqual(len(tickets), 1)
		self.assertEqual(tickets[0]["name"], "SUP-2026-00001")

		tool, args = mcp.call_tool.call_args[0]
		self.assertEqual(tool, "get_list")
		self.assertEqual(args["doctype"], "Support Ticket")
		self.assertEqual(args["filters"], {"status": "Pending"})
		self.assertIn("description", args["fields"])

	def test_error_result_raises(self):
		from helpdesk.ticket_puller import _pending_tickets

		mcp = MagicMock()
		mcp.call_tool.return_value = {"content": [], "isError": True}

		with self.assertRaises(ValueError):
			_pending_tickets(mcp)


class TestCreateHDTicket(FrappeTestCase):
	def test_creates_hd_ticket_from_pulled_payload(self):
		from helpdesk.ticket_puller import _create_hd_ticket

		hd_name = _create_hd_ticket(
			connection_name="QCS-CONN-TEST",
			customer=None,
			ticket={
				"name": "SUP-2026-00001",
				"subject": "Printer offline",
				"description": "<p>offline</p>",
				"raised_by": "user@avientek.com",
			},
		)

		hd = frappe.get_doc("HD Ticket", hd_name)
		self.assertEqual(hd.subject, "Printer offline")
		self.assertEqual(hd.custom_client_ticket, "SUP-2026-00001")
		self.assertEqual(hd.custom_qcs_connection, "QCS-CONN-TEST")

	def test_already_imported_guard(self):
		from helpdesk.ticket_puller import _already_imported, _create_hd_ticket

		_create_hd_ticket(
			connection_name="QCS-CONN-DUPE",
			customer=None,
			ticket={"name": "SUP-2026-00099", "subject": "Dupe check", "description": ""},
		)

		self.assertTrue(_already_imported("QCS-CONN-DUPE", "SUP-2026-00099"))
		self.assertFalse(_already_imported("QCS-CONN-DUPE", "SUP-2026-00100"))


class TestAttachRecording(FrappeTestCase):
	def test_skips_when_absent(self):
		from helpdesk.ticket_puller import _attach_recording

		self.assertIsNone(_attach_recording(MagicMock(), "HD-TICKET-0001", None))


class TestPushBack(FrappeTestCase):
	def test_writes_status_and_ticket_id(self):
		from helpdesk.ticket_puller import _push_back

		mcp = MagicMock()
		mcp.call_tool.return_value = mcp_result({"name": "SUP-2026-00001"})

		_push_back(mcp, "SUP-2026-00001", {"ticket_id": "42", "status": "Open"})

		tool, args = mcp.call_tool.call_args[0]
		self.assertEqual(tool, "set_values")
		self.assertEqual(args["doctype"], "Support Ticket")
		self.assertEqual(args["name"], "SUP-2026-00001")
		self.assertEqual(args["values"]["status"], "Open")
		self.assertEqual(args["values"]["ticket_id"], "42")


class TestSchedulerWiring(FrappeTestCase):
	def test_pull_and_push_are_scheduled_every_five_minutes(self):
		cron = frappe.get_hooks("scheduler_events", app_name="helpdesk").get("cron", {})
		jobs = cron.get("*/5 * * * *", [])
		self.assertIn("helpdesk.tasks.pull_client_tickets", jobs)
		self.assertIn("helpdesk.tasks.push_ticket_statuses", jobs)


class TestInstallFixes(FrappeTestCase):
	def test_illegal_check_default_is_normalised(self):
		"""Helpdesk ships raised_outside_working_hours with default 'False',
		which blocks installing this app onto a fresh Helpdesk site."""
		from helpdesk.install import normalise_illegal_check_defaults

		frappe.db.set_value(
			"DocField",
			{"parent": "HD Ticket", "fieldname": "raised_outside_working_hours"},
			"default",
			"False",
			update_modified=False,
		)

		normalise_illegal_check_defaults()

		self.assertEqual(
			frappe.db.get_value(
				"DocField",
				{"parent": "HD Ticket", "fieldname": "raised_outside_working_hours"},
				"default",
			),
			"0",
		)

	def test_normalise_is_idempotent(self):
		from helpdesk.install import normalise_illegal_check_defaults

		normalise_illegal_check_defaults()
		normalise_illegal_check_defaults()

		self.assertIn(
			frappe.db.get_value(
				"DocField",
				{"parent": "HD Ticket", "fieldname": "raised_outside_working_hours"},
				"default",
			),
			("0", "1"),
		)
