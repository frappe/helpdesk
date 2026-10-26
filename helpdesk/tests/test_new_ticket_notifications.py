"""Agents get a "New Ticket" Notification Log row for every ticket they can open."""

from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase, change_settings

from helpdesk.test_utils import (
    create_agent,
    create_contact,
    get_new_ticket_notifications,
    make_team,
    make_ticket,
    unique_email,
    unique_name,
)


class TestNewTicketNotifications(FrappeTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.agent_one = create_agent(unique_email("new-ticket-agent-one")).name
        cls.agent_two = create_agent(unique_email("new-ticket-agent-two")).name
        cls.inactive_agent = create_agent(unique_email("new-ticket-inactive")).name
        frappe.db.set_value("HD Agent", cls.inactive_agent, "is_active", 0)
        cls.customer = unique_email("new-ticket-customer")
        create_contact("New Ticket Customer", cls.customer)

    def test_every_active_agent_is_notified(self):
        # saved as Administrator, as an email pull does
        ticket = make_ticket(
            subject="Printer <b>on fire</b> & smoking", raised_by=self.customer
        )

        rows = get_new_ticket_notifications(ticket.name)
        self.assertIn(self.agent_one, rows)
        self.assertIn(self.agent_two, rows)
        self.assertNotIn(self.inactive_agent, rows)

        row = rows[self.agent_one]
        self.assertEqual(row.title, f"New ticket #{ticket.name}")
        # saving sanitized the subject's markup already; it must not be escaped again
        self.assertEqual(row.description, ticket.subject)
        self.assertEqual(row.from_user, self.customer, "the requester stands in")
        self.assertEqual(row.app, "helpdesk")
        self.assertFalse(row.read)

    def test_agent_who_creates_the_ticket_is_not_notified(self):
        with self.set_user(self.agent_one):
            ticket = make_ticket(raised_by=self.customer)

        rows = get_new_ticket_notifications(ticket.name)
        self.assertNotIn(self.agent_one, rows)
        self.assertIn(self.agent_two, rows)
        self.assertEqual(rows[self.agent_two].from_user, self.agent_one)

    def test_requester_without_a_user_leaves_sender_empty(self):
        ticket = make_ticket(raised_by=unique_email("new-ticket-stranger"))
        rows = get_new_ticket_notifications(ticket.name)
        self.assertIsNone(rows[self.agent_one].from_user)

    def test_team_restriction_skips_agents_outside_the_team(self):
        team = make_team(unique_name("New Ticket Team"), members=[self.agent_one])
        with change_settings(
            "HD Settings",
            {
                "restrict_tickets_by_agent_group": 1,
                "do_not_restrict_tickets_without_an_agent_group": 0,
            },
        ):
            ticket = make_ticket(raised_by=self.customer, agent_group=team.name)

        rows = get_new_ticket_notifications(ticket.name)
        self.assertIn(self.agent_one, rows)
        self.assertNotIn(self.agent_two, rows)

    def test_initial_email_sync_does_not_notify(self):
        with patch.dict(frappe.flags, {"initial_sync": True}):
            ticket = make_ticket(raised_by=self.customer)
        self.assertEqual(get_new_ticket_notifications(ticket.name), {})
