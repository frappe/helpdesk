# Copyright (c) 2023, Frappe Technologies and Contributors
# See license.txt

import frappe
from frappe.desk.form.assign_to import add as assign
from frappe.tests.utils import FrappeTestCase


def get_ticket_obj():
    return {
        "doctype": "HD Ticket",
        "subject": "Test Ticket",
        "description": "Test Ticket Description",
    }


non_agent = "non_agent@test.com"
agent = "agent@test.com"
agent2 = "agent2@test.com"


class TestHDTicket(FrappeTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        frappe.db.delete("HD Ticket")
        frappe.get_doc(
            {"doctype": "User", "first_name": "Non Agent", "email": non_agent}
        ).insert()

        frappe.get_doc(
            {"doctype": "User", "first_name": "Agent", "email": agent}
        ).insert()
        frappe.get_doc({"doctype": "HD Agent", "user": agent}).insert()

        frappe.get_doc(
            {"doctype": "User", "first_name": "Agent2", "email": agent2}
        ).insert()
        frappe.get_doc({"doctype": "HD Agent", "user": agent2}).insert()

    def test_ticket_creation(self):
        ticket = frappe.get_doc(get_ticket_obj())
        ticket.insert()
        self.assertTrue(ticket.name)

    def test_agent_flow(self):
        ticket = frappe.get_doc(get_ticket_obj())
        ticket.insert()

        ticket.assign_agent(agent)
        ticket.assign_agent(agent2)
        notification = frappe.get_all(
            "HD Notification",
            filters={
                "reference_ticket": ticket.name,
                "notification_type": "Assignment",
                "user_to": ["in", [agent, agent2]],
                "user_from": "Administrator",
            },
        )
        self.assertEqual(len(notification), 2)

        ticket.status = "Replied"
        ticket.save()

        ticket.status = "Open"
        ticket.save()
        self.assertTrue(ticket)

        notification = frappe.get_all(
            "HD Notification",
            filters={
                "reference_ticket": ticket.name,
                "notification_type": "Reaction",
                "user_to": ["in", [agent, agent2]],
                "user_from": "Administrator",
            },
        )
        self.assertEqual(len(notification), 2)

        ticket.status = "Resolved"
        ticket.save()
        self.assertTrue(ticket)

        ticket.status = "Closed"
        ticket.save()
        self.assertTrue(ticket)

    def test_non_agent_flow(self):
        ticket = frappe.get_doc(get_ticket_obj())
        ticket.insert()

        ticket.assign_agent(non_agent)
        notification = frappe.get_all(
            "HD Notification",
            filters={
                "reference_ticket": ticket.name,
                "notification_type": "Assignment",
                "user_to": non_agent,
                "user_from": "Administrator",
            },
        )
        self.assertEqual(len(notification), 1)

        ticket.status = "Replied"
        ticket.save()
        self.assertTrue(ticket)

        ticket.status = "Open"
        ticket.save()
        self.assertTrue(ticket)

        ticket.status = "Resolved"
        ticket.save()
        self.assertTrue(ticket)

        ticket.status = "Closed"
        ticket.save()
        self.assertTrue(ticket)
