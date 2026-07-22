# Copyright (c) 2022, Frappe Technologies and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from helpdesk.api.contact import delete_contact
from helpdesk.test_utils import create_contact, create_customer, make_ticket


class TestDeleteContact(FrappeTestCase):
    def setUp(self) -> None:
        frappe.set_user("Administrator")

    def tearDown(self) -> None:
        frappe.set_user("Administrator")

    def test_delete_contact_unlinks_tickets_and_invitations(self) -> None:
        email = "delete-contact-unlink@example.com"
        contact, customer, ticket, invitation = self.setup_contact_for_delete(
            "Test Contact Unlink", email
        )

        delete_contact(contact["contact"])

        self.assertFalse(frappe.db.exists("Contact", contact["contact"]))
        ticket.reload()
        self.assertIsNone(ticket.contact)
        invitation.reload()
        self.assertIsNone(invitation.contact)
        self.assertFalse(
            frappe.db.exists(
                "HD Customer Member",
                {"parent": customer.name, "contact_name": contact["contact"]},
            )
        )

    def test_delete_contact_deletes_linked_tickets(self) -> None:
        email = "delete-contact-tickets@example.com"
        contact, _, ticket, invitation = self.setup_contact_for_delete(
            "Test Contact Delete Tickets", email
        )

        delete_contact(contact["contact"], delete_tickets=True)

        self.assertFalse(frappe.db.exists("Contact", contact["contact"]))
        self.assertFalse(frappe.db.exists("HD Ticket", ticket.name))
        invitation.reload()
        self.assertIsNone(invitation.contact)

    def test_delete_contact_clears_customer_primary_contact(self) -> None:
        email = "delete-contact-primary@example.com"
        contact_doc, customer, _, _ = self.setup_contact_for_delete(
            "Test Contact Primary", email
        )
        customer.primary_contact = contact_doc["contact"]
        customer.save()

        delete_contact(contact_doc["contact"])

        customer.reload()
        self.assertIsNone(customer.primary_contact)

    def setup_contact_for_delete(self, customer_name: str, email: str):
        for inv in frappe.db.get_all("User Invitation", {"email": email}, pluck="name"):
            frappe.delete_doc("User Invitation", inv, force=True)

        contact = create_contact("DeleteContact", email, user=False)
        customer = create_customer(
            customer_name, [{"contact_name": contact["contact"]}]
        )
        ticket = make_ticket(customer=customer.name, contact=contact["contact"])
        invitation = frappe.get_doc(
            {
                "doctype": "User Invitation",
                "email": email,
                "app_name": "helpdesk",
                "redirect_to_path": "/helpdesk",
                "roles": [{"role": "HD Customer"}],
                "customer": customer.name,
                "contact": contact["contact"],
            }
        ).insert(ignore_permissions=True)
        return contact, customer, ticket, invitation
