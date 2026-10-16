import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.api.ticket_stats import get_feedback_received, get_ticket_stats
from helpdesk.test_utils import create_agent, create_contact, create_customer


class TestTicketStatsPermissions(IntegrationTestCase):
    agent_a = "stats-agent-a@example.com"
    agent_b = "stats-agent-b@example.com"
    manager = "stats-agent-manager@example.com"

    def setUp(self) -> None:
        create_agent(self.agent_a)
        create_agent(self.agent_b)
        create_agent(self.manager)
        frappe.get_doc("User", self.manager).add_roles("Agent Manager")
        frappe.set_user("Administrator")

    def tearDown(self) -> None:
        frappe.set_user("Administrator")

    def test_agent_cannot_view_another_agents_stats(self) -> None:
        # The core leak: a plain agent reading a peer's numbers by passing their
        # email as the agent-scope value.
        frappe.set_user(self.agent_a)
        with self.assertRaises(frappe.PermissionError):
            get_feedback_received(scope="agent", value=self.agent_b)

    def test_agent_can_view_own_stats(self) -> None:
        frappe.set_user(self.agent_a)
        self.assertIn("data", get_feedback_received(scope="agent", value=self.agent_a))

    def test_agent_manager_can_view_any_agent_stats(self) -> None:
        frappe.set_user(self.manager)
        self.assertIn("data", get_feedback_received(scope="agent", value=self.agent_a))

    def test_agent_can_view_customer_and_contact_stats(self) -> None:
        # Customer/contact scope stays open to agents (they already see those
        # records), so the analytics pages keep working.
        customer = create_customer("Stats Customer")
        contact = create_contact("StatsContact", "stats-contact@example.com")
        frappe.set_user(self.agent_a)
        self.assertIn(
            "feedback_received", get_ticket_stats("HD Customer", customer.name)
        )
        self.assertIn(
            "data", get_feedback_received(scope="contact", value=contact["contact"])
        )

    def test_invalid_scope_is_rejected(self) -> None:
        frappe.set_user(self.agent_a)
        with self.assertRaises(frappe.ValidationError):
            get_feedback_received(scope="team", value="anything")
