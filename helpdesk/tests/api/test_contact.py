# Copyright (c) 2022, Frappe Technologies and Contributors
# See license.txt

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.api.contact import delete_contact, get_contact_info
from helpdesk.test_utils import (
    create_agent,
    create_contact,
    create_customer,
    make_contact_invitation,
    make_ticket,
    unique_email,
)


class TestDeleteContact(IntegrationTestCase):
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


class TestContactInvitations(IntegrationTestCase):
    def setUp(self) -> None:
        frappe.set_user("Administrator")
        self.enterContext(self.freeze_time("2026-01-05 10:00:00.123456"))
        self.enterContext(patch("frappe.sendmail"))
        self.email = unique_email("contact-invitation")
        self.contact = create_contact("Invitation Contact", self.email, user=False)[
            "contact"
        ]
        self.agent = create_agent(unique_email("contact-invitation-agent")).name
        self.invitation = make_contact_invitation(self.contact, self.email)

    def test_cancelled_invitation_is_omitted_from_contact_info(self) -> None:
        self.assertTrue(self.invitation.cancel_invite())
        self.invitation.reload()
        self.assertEqual(self.invitation.status, "Cancelled")

        with self.set_user(self.agent):
            self.assertNotIn("invitation", get_contact_info(self.contact))

    def test_pending_and_expired_invitations_remain_visible(self) -> None:
        for status in ("Pending", "Expired"):
            with self.subTest(status=status):
                if status == "Expired":
                    self.invitation.expire()
                with self.set_user(self.agent):
                    invitation = get_contact_info(self.contact)["invitation"]
                self.assertEqual(invitation.name, self.invitation.name)
                self.assertEqual(invitation.status, status)

    def test_cancellation_does_not_revive_an_older_expired_invitation(self) -> None:
        self.invitation.expire()
        with self.freeze_time("2026-01-05 10:01:00.123456"):
            invitation = make_contact_invitation(self.contact, self.email)
            self.assertTrue(invitation.cancel_invite())

        with self.set_user(self.agent):
            self.assertNotIn("invitation", get_contact_info(self.contact))

    def test_new_invitation_is_visible_after_cancellation(self) -> None:
        self.assertTrue(self.invitation.cancel_invite())
        with self.freeze_time("2026-01-05 10:01:00.123456"):
            new_invitation = make_contact_invitation(self.contact, self.email)

        with self.set_user(self.agent):
            invitation = get_contact_info(self.contact)["invitation"]
        self.assertEqual(invitation.name, new_invitation.name)
        self.assertEqual(invitation.status, "Pending")
