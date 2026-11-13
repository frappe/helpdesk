from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.api.ticket import bulk_reply
from helpdesk.test_utils import make_agent, make_ticket, upload_test_file


class TestBulkReplyOutcomes(IntegrationTestCase):
    def setUp(self):
        frappe.set_user("Administrator")
        self.agent = make_agent("bulk-reply-outcomes@test.com")

    def tearDown(self):
        frappe.set_user("Administrator")

    def test_bulk_reply_empty_batch_returns_outcomes(self):
        frappe.set_user(self.agent)
        self.assertEqual(bulk_reply([], "Reply"), {"sent": [], "failed": []})

    def test_bulk_reply_all_failed_leaves_attachment_unlinked(self):
        frappe.set_user(self.agent)
        ticket = make_ticket(raised_by="customer1@test.com")
        file_name = upload_test_file("outlook.png")
        with patch(
            "helpdesk.helpdesk.doctype.hd_ticket.hd_ticket.HDTicket.reply_via_agent",
            side_effect=frappe.ValidationError("No outgoing account"),
        ):
            result = bulk_reply([ticket.name], "Reply", [file_name])
        self.assertEqual(
            result,
            {
                "sent": [],
                "failed": [{"ticket_id": ticket.name, "error": "No outgoing account"}],
            },
        )
        self.assertFalse(frappe.db.get_value("File", file_name, "attached_to_name"))
        frappe.delete_doc("File", file_name)

    def test_bulk_reply_retry_preserves_successful_ticket_attachment(self):
        frappe.set_user(self.agent)
        first = make_ticket(raised_by="customer1@test.com")
        retry = make_ticket(raised_by="customer2@test.com")
        file_name = upload_test_file("outlook.png")
        file_url = frappe.db.get_value("File", file_name, "file_url")
        with patch(
            "helpdesk.helpdesk.doctype.hd_ticket.hd_ticket.HDTicket.reply_via_agent",
            side_effect=[
                "communication",
                frappe.ValidationError("SMTP unavailable"),
                "communication",
            ],
        ):
            result = bulk_reply([first.name, retry.name], "Reply", [file_name])
            self.assertEqual(result["sent"], [first.name])
            self.assertEqual(
                result["failed"],
                [{"ticket_id": retry.name, "error": "SMTP unavailable"}],
            )
            self.assertFalse(
                frappe.db.exists(
                    "File", {"file_url": file_url, "attached_to_name": retry.name}
                )
            )
            self.assertEqual(
                bulk_reply([retry.name], "Reply", [file_name]),
                {"sent": [retry.name], "failed": []},
            )
        self.assertEqual(
            frappe.db.get_value("File", file_name, "attached_to_name"), first.name
        )
        retry_file = frappe.db.get_value(
            "File",
            {
                "file_url": file_url,
                "attached_to_doctype": "HD Ticket",
                "attached_to_name": retry.name,
            },
            "name",
        )
        self.assertTrue(retry_file)
        self.assertNotEqual(retry_file, file_name)
        frappe.delete_doc("File", retry_file)
        frappe.delete_doc("File", file_name)

    def test_bulk_reply_failure_rolls_back_attachments(self):
        frappe.set_user(self.agent)
        failed = make_ticket(raised_by="customer1@test.com")
        sent = make_ticket(raised_by="customer2@test.com")
        file_name = upload_test_file("outlook.png")
        with patch(
            "helpdesk.helpdesk.doctype.hd_ticket.hd_ticket.HDTicket.reply_via_agent",
            side_effect=[
                frappe.ValidationError("No outgoing account"),
                "communication",
            ],
        ):
            result = bulk_reply([failed.name, sent.name], "Reply", [file_name])
        self.assertEqual(result["sent"], [sent.name])
        self.assertEqual(
            result["failed"],
            [{"ticket_id": failed.name, "error": "No outgoing account"}],
        )
        self.assertFalse(
            frappe.db.exists(
                "File",
                {"attached_to_doctype": "HD Ticket", "attached_to_name": failed.name},
            )
        )
        self.assertEqual(
            frappe.db.get_value("File", file_name, "attached_to_name"), sent.name
        )
        frappe.delete_doc("File", file_name)
