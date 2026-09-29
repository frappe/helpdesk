# Copyright (c) 2022, Frappe Technologies and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.api.contact import delete_contact, get_related_tickets
from helpdesk.test_utils import (
    create_contact,
    create_customer,
    make_communication,
    make_ticket,
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


class TestGetRelatedTickets(IntegrationTestCase):
    def setUp(self) -> None:
        frappe.set_user("Administrator")

    def tearDown(self) -> None:
        frappe.set_user("Administrator")

    def test_returns_a_ticket_the_contact_was_cced_on(self) -> None:
        email = "cced-contact@example.com"
        contact = create_contact("CcedContact", email, user=False)
        ticket = make_ticket(subject="Cced ticket")
        make_communication(
            ticket.name, sender="bob@client.com", recipients="support@work.com",
            cc=f"Other <{email}>",
        )

        related = get_related_tickets(contact["contact"])

        self.assertIn(ticket.name, [t.name for t in related])

    def test_returns_a_ticket_the_contact_was_sent_to(self) -> None:
        email = "sent-to-contact@example.com"
        contact = create_contact("SentToContact", email, user=False)
        ticket = make_ticket(subject="Sent to ticket")
        make_communication(
            ticket.name, sender="bob@client.com", recipients=email,
        )

        related = get_related_tickets(contact["contact"])

        self.assertIn(ticket.name, [t.name for t in related])

    def test_returns_a_ticket_the_contact_replied_on_as_sender(self) -> None:
        email = "replier-contact@example.com"
        contact = create_contact("ReplierContact", email, user=False)
        ticket = make_ticket(subject="Replied on ticket")
        make_communication(
            ticket.name, sender=email, recipients="support@work.com",
        )

        related = get_related_tickets(contact["contact"])

        self.assertIn(ticket.name, [t.name for t in related])

    def test_ignores_an_address_that_merely_contains_the_contact_email(self) -> None:
        """'an@example.com' is a substring of 'dan@example.com', so a raw
        LIKE '%email%' would wrongly claim the contact was involved."""
        contact = create_contact("ShortContact", "an@example.com", user=False)
        ticket = make_ticket(subject="Someone else's ticket")
        make_communication(
            ticket.name, sender="bob@client.com", recipients="dan@example.com",
        )

        related = get_related_tickets(contact["contact"])

        self.assertNotIn(ticket.name, [t.name for t in related])

    def test_treats_underscore_in_contact_email_literally(self) -> None:
        """'_' is a single-character wildcard to SQL LIKE, so an unescaped
        filter would match 'bobyx@example.com' for 'bob_x@example.com'."""
        contact = create_contact("UnderscoreContact", "bob_x@example.com", user=False)
        ticket = make_ticket(subject="Wildcard collision ticket")
        make_communication(
            ticket.name, sender="someone@client.com", recipients="bobyx@example.com",
        )

        related = get_related_tickets(contact["contact"])

        self.assertNotIn(ticket.name, [t.name for t in related])

    def test_matches_a_quoted_display_name_containing_a_comma(self) -> None:
        """A naive split(',') would break this header into bad addresses."""
        contact = create_contact("QuotedContact", "kelly@work.com", user=False)
        ticket = make_ticket(subject="Quoted display name ticket")
        make_communication(
            ticket.name,
            sender="bob@client.com",
            recipients='"Doe, Kelly" <kelly@work.com>, jane@client.com',
        )

        related = get_related_tickets(contact["contact"])

        self.assertIn(ticket.name, [t.name for t in related])

    def test_excludes_tickets_the_contact_already_owns(self) -> None:
        email = "owner-contact@example.com"
        contact = create_contact("OwnerContact", email, user=False)
        ticket = make_ticket(subject="Owned ticket", contact=contact["contact"])
        make_communication(
            ticket.name, sender=email, recipients="support@work.com",
        )

        related = get_related_tickets(contact["contact"])

        self.assertNotIn(ticket.name, [t.name for t in related])
