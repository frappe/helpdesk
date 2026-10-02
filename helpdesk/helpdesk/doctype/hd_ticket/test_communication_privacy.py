import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.test_utils import (
    create_contact,
    get_communication_as,
    make_agent,
    make_customer_ticket,
    make_email_with_bcc,
)

CUSTOMER = "privacy.customer@example.com"
AGENT = "privacy.agent@example.com"
CC = "colleague@example.com"
BCC = "hidden@example.com"


class TestCommunicationPrivacy(IntegrationTestCase):
    def setUp(self):
        frappe.set_user("Administrator")
        create_contact("Privacy Customer", CUSTOMER)
        make_agent(AGENT)
        self.ticket = make_customer_ticket(self, raised_by=CUSTOMER)
        self.email = make_email_with_bcc(self, self.ticket, AGENT, BCC, CC)

    def test_customer_does_not_receive_bcc(self):
        email = get_communication_as(CUSTOMER, self.ticket.name, self.email)
        self.assertNotIn(BCC, str(email.get("bcc") or ""))
        self.assertEqual(email.cc, CC)

    def test_agent_receives_bcc(self):
        email = get_communication_as(AGENT, self.ticket.name, self.email)
        self.assertEqual(email.bcc, BCC)

    def test_agent_as_requester_does_not_receive_bcc(self):
        ticket = make_customer_ticket(self, raised_by=AGENT)
        email_name = make_email_with_bcc(self, ticket, AGENT, BCC)
        email = get_communication_as(AGENT, ticket.name, email_name)
        self.assertNotIn(BCC, str(email.get("bcc") or ""))
