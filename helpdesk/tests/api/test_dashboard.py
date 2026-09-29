import json

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, now_datetime, nowdate

from helpdesk.api.dashboard import HelpdeskDashboard
from helpdesk.test_utils import create_agent, make_sla, make_ticket

AGENT = "dashboard-sla-agent@example.com"


class TestSlaFulfilledCard(IntegrationTestCase):
    def test_fulfilled_percentage_stays_within_100(self):
        """A response-only policy marks a still-open ticket Fulfilled. Counting it
        in the numerator while the denominator only holds resolved tickets pushes
        the card past 100%."""
        create_agent(AGENT)
        response_only = make_sla("Response Only", "doc.subject == 'Response only'", 1)
        response_only.apply_sla_for_resolution = 0
        response_only.save()

        open_ticket = self.make_assigned_ticket("Response only")
        self.assertEqual(open_ticket.agreement_status, "Fulfilled")
        self.assertNotEqual(open_ticket.status_category, "Resolved")

        resolved_ticket = self.make_assigned_ticket("Resolved one", status="Closed")
        self.assertEqual(resolved_ticket.agreement_status, "Fulfilled")

        card = self.get_sla_card()
        self.assertEqual(card["value"], 100)

    def make_assigned_ticket(self, subject: str, status: str | None = None):
        """A ticket that has been responded to, scoped to this test's agent."""
        ticket = make_ticket(subject=subject)
        ticket.reload()
        ticket.first_responded_on = now_datetime()
        if status:
            ticket.status = status
        ticket.save()
        frappe.db.set_value("HD Ticket", ticket.name, "_assign", json.dumps([AGENT]))
        return ticket

    def get_sla_card(self) -> dict:
        filters = frappe._dict(
            from_date=add_days(nowdate(), -1), to_date=nowdate(), agent=AGENT
        )
        return HelpdeskDashboard(filters).get_sla_fulfilled_count()
