from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_to_date, now_datetime

from helpdesk.helpdesk.doctype.hd_ticket.api import merge_ticket, split_ticket
from helpdesk.integrations.whatsapp.merge import send_merge_notice
from helpdesk.integrations.whatsapp.outgoing import NEW_TICKET_BUTTON
from helpdesk.integrations.whatsapp.test_utils import (
    META_REQUEST,
    make_whatsapp_account,
    mock_meta,
    press_button,
    receive_message,
    requires_whatsapp,
    sent_payloads,
)
from helpdesk.test_utils import make_ticket

CUSTOMER_NUMBER = "919800000101"
OTHER_NUMBER = "919800000102"
NOTICE_JOB = "helpdesk.integrations.whatsapp.merge.send_merge_notice"


@requires_whatsapp
class TestWhatsAppMerge(IntegrationTestCase):
    def setUp(self) -> None:
        self.account = make_whatsapp_account()
        self.source = self.open_ticket(CUSTOMER_NUMBER, self.account)
        self.target = self.open_new_ticket_after_closing(self.source)

    def tearDown(self) -> None:
        frappe.set_user("Administrator")
        frappe.db.rollback()

    def test_refuses_merges_across_channels(self) -> None:
        email_ticket = make_ticket(raised_by="merge.channel@example.com").name
        for source, target in (
            (self.source, email_ticket),
            (email_ticket, self.source),
        ):
            with self.assertRaisesRegex(
                frappe.ValidationError, "another WhatsApp ticket"
            ):
                merge_ticket(source=source, target=target)
        self.assertFalse(frappe.db.get_value("HD Ticket", self.source, "is_merged"))

    def test_refuses_merges_across_business_numbers(self) -> None:
        other = self.open_ticket(CUSTOMER_NUMBER, make_whatsapp_account())
        with self.assertRaisesRegex(frappe.ValidationError, "share a business number"):
            merge_ticket(source=self.source, target=other)

    def test_refuses_merges_across_customers(self) -> None:
        other = self.open_ticket(OTHER_NUMBER, self.account)
        with self.assertRaisesRegex(frappe.ValidationError, "same customer"):
            merge_ticket(source=self.source, target=other)

    def test_moves_messages_and_notifies_the_source_customer(self) -> None:
        source_messages = self.message_names(self.source)
        total = frappe.db.count("WA Message")
        with mock_meta() as meta:
            jobs = self.merge_capturing_notice_jobs()
            self.assertEqual(sent_payloads(meta), [])
            self.assertEqual(len(jobs), 1)
            self.assertTrue(jobs[0].kwargs["enqueue_after_commit"])
            send_merge_notice(source=self.source, target=self.target)

        self.assertEqual(len(sent_payloads(meta)), 1)
        self.assertEqual(frappe.db.count("WA Message"), total + 1)
        self.assertEqual(self.message_names(self.source), [])
        self.assertLessEqual(set(source_messages), set(self.message_names(self.target)))
        notice = frappe.get_last_doc("WA Message", {"direction": "Outgoing"})
        customer = frappe.db.get_value("WA Message", source_messages[0], "to")
        self.assertEqual(
            (notice.to, notice.reference_docname, notice.whatsapp_account),
            (customer, self.target, self.account),
        )
        self.assertIn(self.source, notice.message)
        self.assertSlaUntouched(self.target)
        self.assertFalse(
            frappe.db.exists("Communication", {"reference_name": self.source})
        )

    def test_no_notice_once_the_reply_window_closed(self) -> None:
        for name in self.message_names(self.source) + self.message_names(self.target):
            frappe.db.set_value(
                "WA Message",
                name,
                "creation",
                add_to_date(now_datetime(), hours=-25),
                update_modified=False,
            )
        self.assertEqual(self.merge_capturing_notice_jobs(), [])
        self.assertTrue(frappe.db.get_value("HD Ticket", self.source, "is_merged"))

    def test_notice_job_survives_meta_refusing(self) -> None:
        with (
            patch(META_REQUEST, side_effect=frappe.ValidationError("Meta said no")),
            patch("frappe.log_error") as log_error,
        ):
            send_merge_notice(source=self.source, target=self.target)
        log_error.assert_called_once()

    def test_split_refuses_whatsapp_tickets(self) -> None:
        communication = frappe.get_doc(
            {
                "doctype": "Communication",
                "subject": "Stray email",
                "content": "Stray email",
                "communication_medium": "Email",
                "sent_or_received": "Received",
                "reference_doctype": "HD Ticket",
                "reference_name": self.source,
            }
        )
        # skip the hooks, which refuse any email on a WhatsApp ticket
        communication.db_insert()
        with self.assertRaisesRegex(frappe.ValidationError, "cannot be split"):
            split_ticket(subject="Split", communication_id=communication.name)

    def merge_capturing_notice_jobs(self) -> list:
        with patch("frappe.enqueue") as enqueue:
            merge_ticket(source=self.source, target=self.target)
        return [job for job in enqueue.call_args_list if job.args[:1] == (NOTICE_JOB,)]

    def open_ticket(self, number: str, account: str) -> str:
        return receive_message(number, "My order is late", account).reference_docname

    def open_new_ticket_after_closing(self, ticket: str) -> str:
        frappe.db.set_value("HD Ticket", ticket, "status", "Closed")
        with mock_meta():
            receive_message(CUSTOMER_NUMBER, "Another problem", self.account)
            prompt = frappe.get_last_doc("WA Message", {"direction": "Outgoing"})
            answer = press_button(
                CUSTOMER_NUMBER, self.account, prompt.name, NEW_TICKET_BUTTON
            )
        return answer.reference_docname

    def message_names(self, ticket: str) -> list[str]:
        return frappe.get_all(
            "WA Message",
            filters={"reference_doctype": "HD Ticket", "reference_docname": ticket},
            pluck="name",
        )

    def assertSlaUntouched(self, ticket: str) -> None:
        stamps = frappe.db.get_value(
            "HD Ticket", ticket, ["first_responded_on", "last_agent_response"]
        )
        self.assertEqual(stamps, (None, None))
