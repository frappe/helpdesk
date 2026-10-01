import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.helpdesk.doctype.hd_ticket.api import get_communications
from helpdesk.test_utils import create_contact, make_agent, make_customer_ticket

CUSTOMER = "privacy.customer@example.com"
AGENT = "privacy.agent@example.com"


class TestCommunicationPrivacy(IntegrationTestCase):
    def setUp(self):
        frappe.set_user("Administrator")
        create_contact("Privacy Customer", CUSTOMER)
        make_agent(AGENT)
        self.ticket = make_customer_ticket(self, raised_by=CUSTOMER)
        self.email = self.email_with_bcc(self.ticket)

    def email_with_bcc(self, ticket):
        email = frappe.get_doc(
            {
                "doctype": "Communication",
                "communication_type": "Communication",
                "communication_medium": "Email",
                "sent_or_received": "Sent",
                "sender": AGENT,
                "recipients": CUSTOMER,
                "cc": "colleague@example.com",
                "bcc": "hidden@example.com",
                "subject": ticket.subject,
                "content": "<p>Reply</p>",
                "reference_doctype": "HD Ticket",
                "reference_name": ticket.name,
            }
        ).insert(ignore_permissions=True)
        self.addCleanup(frappe.delete_doc, "Communication", email.name, force=True)
        return email.name

    def tearDown(self):
        frappe.set_user("Administrator")

    def communication(self, user, ticket=None, email=None):
        frappe.set_user(user)
        ticket, email = ticket or self.ticket, email or self.email
        return next(c for c in get_communications(ticket.name) if c.name == email)

    def test_customer_does_not_receive_bcc(self):
        email = self.communication(CUSTOMER)
        self.assertNotIn("hidden@example.com", str(email.get("bcc") or ""))
        self.assertEqual(email.cc, "colleague@example.com")

    def test_agent_receives_bcc(self):
        email = self.communication(AGENT)
        self.assertEqual(email.bcc, "hidden@example.com")

    def test_agent_as_requester_does_not_receive_bcc(self):
        ticket = make_customer_ticket(self, raised_by=AGENT)
        email = self.email_with_bcc(ticket)
        self.assertNotIn(
            "hidden@example.com",
            str(self.communication(AGENT, ticket, email).get("bcc") or ""),
        )
