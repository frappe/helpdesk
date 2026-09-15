# Copyright (c) 2025, Frappe Technologies and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.test_utils import create_contact, make_ticket

CUSTOMER = "email-feedback-customer@example.com"


class IntegrationTestHDEmailFeedback(IntegrationTestCase):
    """The feedback mail goes out on close, so every rating it invites lands on
    a ticket the customer is otherwise forbidden to touch."""

    def setUp(self):
        frappe.set_user("Administrator")
        self.addCleanup(frappe.set_user, "Administrator")
        create_contact("Feedback Customer", CUSTOMER)

    def delete_as_administrator(self, doctype: str, name: str):
        # cleanups run before the set_user reset, whatever user the test ended as
        frappe.set_user("Administrator")
        frappe.delete_doc(doctype, name, force=True)

    def close_emailed_ticket(self) -> str:
        """Only a ticket that arrived by email is ever sent a feedback link."""
        ticket = make_ticket(subject="Feedback flow", raised_by=CUSTOMER)
        self.addCleanup(self.delete_as_administrator, "HD Ticket", ticket.name)
        frappe.db.set_value("HD Ticket", ticket.name, "via_customer_portal", 0)

        doc = frappe.get_doc("HD Ticket", ticket.name)
        doc.status = "Closed"
        doc.save()
        return doc.name

    def submit_feedback(self, key: str, rating: float):
        feedback = frappe.get_doc(
            doctype="HD Email Feedback",
            key=key,
            feedback_rating=rating,
            feedback_extra="all good",
        )
        feedback.insert(ignore_permissions=True)
        self.addCleanup(
            self.delete_as_administrator, "HD Email Feedback", feedback.name
        )

    def test_a_guest_can_rate_a_closed_ticket_from_the_email(self):
        name = self.close_emailed_ticket()
        key = frappe.db.get_value("HD Ticket", name, "key")

        frappe.set_user("Guest")
        self.submit_feedback(key, 0.6)

        frappe.set_user("Administrator")
        self.assertEqual(frappe.db.get_value("HD Ticket", name, "feedback_rating"), 0.6)

    def test_rating_does_not_let_a_customer_edit_the_closed_ticket(self):
        """The exemption covers the rating, not the ticket it is attached to."""
        name = self.close_emailed_ticket()

        frappe.set_user(CUSTOMER)
        doc = frappe.get_doc("HD Ticket", name)
        doc.subject = "edited after closing"
        with self.assertRaises(frappe.PermissionError):
            doc.save()
