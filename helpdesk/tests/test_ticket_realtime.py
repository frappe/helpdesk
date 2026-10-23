"""Customers can't join a ticket's socket room, so each reader gets a bare ping on their own channel."""

from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from helpdesk.test_utils import (
    create_customer,
    make_agent,
    make_contact,
    make_ticket,
    make_todo,
    ticket_pings,
    unique_email,
    unique_name,
)


class TestTicketRealtime(FrappeTestCase):
    def setUp(self):
        self.agent = make_agent(unique_email("realtime-agent"))
        self.requester = make_contact("realtime-customer")
        self.manager = make_contact("realtime-customer")
        self.colleague = make_contact("realtime-customer")
        self.customer = create_customer(
            unique_name("Realtime Org"),
            contacts=[
                {"contact_name": self.requester["contact"], "is_manager": 0},
                {"contact_name": self.manager["contact"], "is_manager": 1},
                {"contact_name": self.colleague["contact"], "is_manager": 0},
            ],
        ).name
        self.outsider = make_contact("realtime-customer")
        create_customer(
            unique_name("Other Org"),
            contacts=[{"contact_name": self.outsider["contact"], "is_manager": 1}],
        )
        self.ticket = make_ticket(
            raised_by=self.requester["user"], customer=self.customer
        )

    def pings_for(self, change):
        with patch("frappe.publish_realtime") as publish_realtime:
            change()
        return ticket_pings(publish_realtime)

    def save_as(self, user):
        def change():
            with self.set_user(user):
                doc = frappe.get_doc("HD Ticket", self.ticket.name)
                doc.priority = doc.priority
                doc.save(ignore_permissions=True)

        return change

    def test_agent_change_pings_requester_and_managers_only(self):
        pings = self.pings_for(self.save_as(self.agent))
        self.assertEqual(pings, {self.requester["user"], self.manager["user"]})

    def test_customer_is_not_pinged_for_their_own_change(self):
        pings = self.pings_for(self.save_as(self.requester["user"]))
        self.assertEqual(pings, {self.manager["user"]})

    def test_agents_and_guest_are_never_pinged(self):
        ticket = make_ticket(raised_by=self.agent)

        def change():
            doc = frappe.get_doc("HD Ticket", ticket.name)
            doc.save(ignore_permissions=True)

        with self.set_user("Guest"):
            pings = self.pings_for(change)
        self.assertEqual(pings, set())

    def test_disabled_reader_is_skipped(self):
        frappe.db.set_value("User", self.manager["user"], "enabled", 0)
        pings = self.pings_for(self.save_as(self.agent))
        self.assertEqual(pings, {self.requester["user"]})

    def test_deleting_pings_the_readers_it_had(self):
        pings = self.pings_for(
            lambda: frappe.delete_doc("HD Ticket", self.ticket.name, force=True)
        )
        self.assertEqual(pings, {self.requester["user"], self.manager["user"]})

    def test_assignment_pings_readers(self):
        pings = self.pings_for(lambda: make_todo(self.ticket.name, self.agent))
        self.assertEqual(pings, {self.requester["user"], self.manager["user"]})

    def test_automated_message_pings_readers(self):
        def change():
            frappe.get_doc(
                {
                    "doctype": "Communication",
                    "communication_type": "Automated Message",
                    "communication_medium": "Email",
                    "sent_or_received": "Sent",
                    "subject": "We got your ticket",
                    "content": "We got your ticket",
                    "reference_doctype": "HD Ticket",
                    "reference_name": self.ticket.name,
                }
            ).insert(ignore_permissions=True)

        pings = self.pings_for(change)
        self.assertEqual(pings, {self.requester["user"], self.manager["user"]})
