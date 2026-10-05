from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.api import ticket as ticket_api
from helpdesk.api.ticket import get_guest_draft
from helpdesk.test_utils import (
    create_user,
    emails_queued_to,
    enable_guest_tickets,
    get_invitation,
    guest_draft_tokens,
    submit_guest_form,
    unique_email,
)


class TestGuestTicket(IntegrationTestCase):
    def setUp(self):
        frappe.set_user("Administrator")
        self.addCleanup(
            enable_guest_tickets,
            frappe.db.get_single_value("HD Settings", "allow_anyone_to_create_tickets"),
        )
        enable_guest_tickets()

    def tearDown(self):
        frappe.set_user("Administrator")

    def guest_tickets(self, email: str) -> list[dict]:
        return frappe.get_all(
            "HD Ticket", {"raised_by": email}, ["name", "subject", "contact"]
        )

    def test_setting_off_asks_the_guest_to_sign_in(self):
        enable_guest_tickets(False)
        with self.assertRaises(frappe.PermissionError):
            submit_guest_form(self, unique_email("off"))

    def test_a_new_email_gets_a_ticket_a_contact_and_one_invite(self):
        email = unique_email("new")
        submit_guest_form(self, f"  {email.upper()} ", first_name="Jane")
        submit_guest_form(self, email, subject="Still offline")

        tickets = self.guest_tickets(email)
        self.assertEqual(len(tickets), 2)
        contact = frappe.db.get_value("Contact", {"email_id": email})
        self.assertEqual({t.contact for t in tickets}, {contact})
        self.assertEqual(frappe.db.get_value("Contact", contact, "first_name"), "Jane")
        self.assertEqual(
            frappe.db.count(
                "User Invitation", {"email": email, "app_name": "helpdesk"}
            ),
            1,
        )

    def test_a_known_contact_without_an_account_is_reused(self):
        email = unique_email("known")
        submit_guest_form(self, email)
        submit_guest_form(self, email)
        self.assertEqual(frappe.db.count("Contact", {"email_id": email}), 1)

    def test_an_account_holder_gets_a_continue_email_not_a_ticket(self):
        email = create_user(unique_email("member")).name
        self.addCleanup(frappe.delete_doc, "User", email, force=True)
        submit_guest_form(self, email, subject="Billing question")

        self.assertEqual(self.guest_tickets(email), [])
        self.assertIsNone(get_invitation(email))
        self.assertEqual(emails_queued_to(email), 1)

        [token] = guest_draft_tokens(email)
        other = create_user(unique_email("other")).name
        self.addCleanup(frappe.delete_doc, "User", other, force=True)
        frappe.set_user(other)
        self.assertIsNone(get_guest_draft(token))
        frappe.set_user(email)
        self.assertEqual(get_guest_draft(token)["subject"], "Billing question")
        self.assertIsNone(get_guest_draft(token))

    def test_continue_emails_are_spaced_out(self):
        email = create_user(unique_email("flooded")).name
        self.addCleanup(frappe.delete_doc, "User", email, force=True)
        submit_guest_form(self, email)
        submit_guest_form(self, email)
        self.assertEqual(emails_queued_to(email), 1)

    def test_an_account_holder_gets_a_ticket_when_mail_cannot_go_out(self):
        email = create_user(unique_email("offline")).name
        self.addCleanup(frappe.delete_doc, "User", email, force=True)
        with patch.object(ticket_api.EmailAccount, "find_outgoing", return_value=None):
            submit_guest_form(self, email)
        self.assertEqual(len(self.guest_tickets(email)), 1)
        self.assertIsNone(get_invitation(email))

    def test_a_disabled_account_gets_a_ticket_and_no_invite(self):
        email = create_user(unique_email("disabled")).name
        self.addCleanup(frappe.delete_doc, "User", email, force=True)
        frappe.db.set_value("User", email, "enabled", 0)
        submit_guest_form(self, email)
        self.assertEqual(len(self.guest_tickets(email)), 1)
        self.assertIsNone(get_invitation(email))

    def test_the_support_address_is_refused(self):
        address = frappe.db.get_value(
            "Email Account", {"email_id": ("is", "set")}, "email_id"
        )
        if not address:
            self.skipTest("no email account on this site")
        with self.assertRaises(frappe.ValidationError):
            submit_guest_form(self, address)

    def test_bad_input_is_refused(self):
        for values in (
            {"email": "not-an-email"},
            {"description": "<p></p>"},
            {"subject": " "},
        ):
            email = values.pop("email", unique_email("bad"))
            with self.assertRaises(frappe.ValidationError):
                submit_guest_form(self, email, **values)

    def test_the_site_wide_cap_stops_guest_tickets(self):
        with patch.object(ticket_api, "GUEST_TICKETS_PER_HOUR", 0):
            with self.assertRaises(frappe.RateLimitExceededError):
                submit_guest_form(self, unique_email("capped"))
