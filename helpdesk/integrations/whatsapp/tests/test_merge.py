import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.helpdesk.doctype.hd_ticket.api import merge_ticket, split_ticket
from helpdesk.integrations.whatsapp.test_utils import (
    make_number,
    make_whatsapp_account,
    receive_message,
    requires_whatsapp,
)
from helpdesk.test_utils import make_ticket


@requires_whatsapp
class TestWhatsAppMerge(IntegrationTestCase):
    def setUp(self) -> None:
        self.account = make_whatsapp_account()
        self.ticket = self.open_ticket()

    def tearDown(self) -> None:
        frappe.set_user("Administrator")
        frappe.db.rollback()

    def test_refuses_any_merge_with_a_whatsapp_ticket(self) -> None:
        email_ticket = make_ticket(raised_by="merge.channel@example.com").name
        for source, target in (
            (self.ticket, email_ticket),
            (email_ticket, self.ticket),
            (self.ticket, self.open_ticket()),
        ):
            with self.assertRaisesRegex(frappe.ValidationError, "cannot be merged"):
                merge_ticket(source=source, target=target)
        self.assertFalse(frappe.db.get_value("HD Ticket", self.ticket, "is_merged"))
        self.assertFalse(frappe.db.get_value("HD Ticket", email_ticket, "is_merged"))

    def test_split_refuses_whatsapp_tickets(self) -> None:
        communication = frappe.get_doc(
            {
                "doctype": "Communication",
                "subject": "Stray email",
                "content": "Stray email",
                "communication_medium": "Email",
                "sent_or_received": "Received",
                "reference_doctype": "HD Ticket",
                "reference_name": self.ticket,
            }
        )
        # skip the hooks, which refuse any email on a WhatsApp ticket
        communication.db_insert()
        with self.assertRaisesRegex(frappe.ValidationError, "cannot be split"):
            split_ticket(subject="Split", communication_id=communication.name)

    def open_ticket(self) -> str:
        return receive_message(
            make_number(), "My order is late", self.account
        ).reference_docname
