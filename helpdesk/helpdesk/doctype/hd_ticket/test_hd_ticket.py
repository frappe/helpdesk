# Copyright (c) 2023, Frappe Technologies and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_to_date, getdate

from helpdesk.test_utils import (
    add_holiday,
    get_current_week_monday,
    get_priority_response_resolution_time,
    make_ticket,
    remove_holidays,
)

ERROR_MSG_RESPONSE = "Response time differs by more than 1 second"
ERROR_MSG_RESOLUTION = "Resolution time differs by more than 1 second"


def get_ticket_obj():
    return {
        "doctype": "HD Ticket",
        "subject": "Test Ticket",
        "description": "Test Ticket Description",
    }


non_agent = "non_agent@test.com"
agent = "agent@test.com"
agent2 = "agent2@test.com"


class TestHDTicket(IntegrationTestCase):
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
        ticket = frappe.get_doc("HD Ticket", ticket.name)
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

        ticket = frappe.get_doc("HD Ticket", ticket.name)
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

    # Working hours default to 10:00 to 18:00 from Monday to Friday
    # And priorities default to
    # Low: 24 hour response, 72 hours resolution
    # Medium: 8 hour response, 24 hours resolution
    # High: 1 hour response, 4 hours resolution
    # Urgent: 30 minutes response, 2 hours resolution

    def test_response_resolution_working_day(self):
        ticket_creation = get_current_week_monday()
        ticket = make_ticket(
            priority="High", service_level_agreement_creation=ticket_creation
        )

        expected_response_by = add_to_date(ticket_creation, hours=1)  # 1 hour later
        expected_resolution_by = add_to_date(ticket_creation, hours=4)  # 4 hours later

        self.assertAlmostEqual(
            expected_response_by.timestamp(),
            ticket.response_by.timestamp(),
            delta=1,
            msg=ERROR_MSG_RESPONSE,
        )
        self.assertAlmostEqual(
            expected_resolution_by.timestamp(),
            ticket.resolution_by.timestamp(),
            delta=1,
            msg=ERROR_MSG_RESOLUTION,
        )

    def test_response_resolution_before_working_hours(self):
        day_start_time_hours = 10
        hours_before_working = 2
        ticket_creation = getdate(get_current_week_monday())
        ticket_creation = add_to_date(
            ticket_creation, hours=day_start_time_hours - hours_before_working
        )  # Monday 8:00 AM

        ticket = make_ticket(
            priority="High", service_level_agreement_creation=ticket_creation
        )

        # high priority has 1 hour response time and 4 hours resolution time
        first_response, resolution = get_priority_response_resolution_time(
            "Default", "High", ticket_creation, add_to_time=False
        )
        # start time = 10:00 AM
        # response time = 11:00 AM
        # resolution time = 14:00 PM
        first_response_hours = day_start_time_hours + (
            first_response / 3600
        )  # 1 hour later
        resolution_hours = day_start_time_hours + (resolution / 3600)  # 4 hours later
        expected_first_response = add_to_date(
            getdate(ticket_creation), hours=first_response_hours
        )  # 11:00 AM
        expected_resolution = add_to_date(
            getdate(ticket_creation), hours=resolution_hours
        )  # 4 hours from 10:00 AM

        self.assertAlmostEqual(
            expected_first_response.timestamp(),
            ticket.response_by.timestamp(),
            delta=1,
            msg=ERROR_MSG_RESPONSE,
        )
        self.assertAlmostEqual(
            expected_resolution.timestamp(),
            ticket.resolution_by.timestamp(),
            delta=1,
            msg=ERROR_MSG_RESOLUTION,
        )

    def test_response_resolution_after_working_hours(self):
        ticket_creation = get_current_week_monday(hours=20)  # Monday 8:00 PM
        ticket = make_ticket(
            priority="Urgent", service_level_agreement_creation=ticket_creation
        )  # 30 minutes response time, 2 hours resolution time
        expected_response_by = add_to_date(
            getdate(ticket_creation), days=1, hours=10, minutes=30
        )  # Tuesday 10:30 AM
        expected_resolution_by = add_to_date(
            getdate(ticket_creation), days=1, hours=12
        )  # Tuesday 12:00 PM

        self.assertAlmostEqual(
            expected_response_by.timestamp(),
            ticket.response_by.timestamp(),
            delta=1,
            msg=ERROR_MSG_RESPONSE,
        )
        self.assertAlmostEqual(
            expected_resolution_by.timestamp(),
            ticket.resolution_by.timestamp(),
            delta=1,
            msg=ERROR_MSG_RESOLUTION,
        )

    def test_response_resolution_non_working_day(self):
        ticket_creation = add_to_date(
            get_current_week_monday(hours=0), days=5, hours=15
        )  # Saturday 3:00 PM
        ticket = make_ticket(
            priority="Low", service_level_agreement_creation=ticket_creation
        )
        response_time, resolution_time = get_priority_response_resolution_time(
            ticket.sla, ticket.priority, add_to_time=False
        )

        expected_response_by = add_to_date(
            getdate(ticket_creation), days=4, hours=18
        )  # Next week wednesday at 6:00 PM
        expected_resolution_by = add_to_date(
            getdate(ticket_creation), days=12, hours=18
        )  # 12 Days after ticket creation at 6:00 PM

        self.assertAlmostEqual(
            expected_response_by.timestamp(),
            ticket.response_by.timestamp(),
            delta=1,
            msg=ERROR_MSG_RESPONSE,
        )
        self.assertAlmostEqual(
            expected_resolution_by.timestamp(),
            ticket.resolution_by.timestamp(),
            delta=1,
            msg=ERROR_MSG_RESOLUTION,
        )

    def test_response_resolution_friday_in_working_hours(self):
        mock_date = add_to_date(
            get_current_week_monday(hours=0), days=4, hours=17
        )  # Friday 5:00 PM
        ticket = make_ticket(
            priority="Urgent", service_level_agreement_creation=mock_date
        )
        expected_response_by = add_to_date(mock_date, minutes=30)  # 30 minutes later
        expected_resolution_by = add_to_date(
            getdate(mock_date), days=3, hours=11
        )  # Monday 11:00 AM, 1 hour from friday and 1 hour from monday

        self.assertEqual(expected_response_by, ticket.response_by)
        self.assertEqual(expected_resolution_by, ticket.resolution_by)

    def test_response_resolution_friday_after_working_hours(self):
        mock_date = add_to_date(
            get_current_week_monday(hours=0), days=4, hours=19
        )  # Friday 7:00 PM

        ticket = make_ticket(
            priority="High", service_level_agreement_creation=mock_date
        )

        expected_response_by = add_to_date(
            getdate(mock_date), days=3, hours=11
        )  # Monday 11:00 AM
        expected_resolution_by = add_to_date(
            getdate(mock_date), days=3, hours=14
        )  # Monday 2:00 PM

        self.assertEqual(expected_response_by, ticket.response_by)
        self.assertEqual(expected_resolution_by, ticket.resolution_by)

    def test_response_resolution_holiday(self):
        mock_date = add_to_date(
            get_current_week_monday(hours=0), days=3, hours=15
        )  # Thursday 3:00 PM
        holiday_date = getdate(mock_date)

        add_holiday(holiday_date, "Test Holiday")  # Thursday is set as a holiday
        add_holiday(
            add_to_date(holiday_date, days=1), "Test Holiday"
        )  # Friday is set as a holiday
        # Saturday and Sunday are already non-working days

        ticket = make_ticket(
            priority="Urgent", service_level_agreement_creation=mock_date
        )

        expected_response_by = add_to_date(
            getdate(mock_date), days=4, hours=10, minutes=30
        )  # Next week Monday at 10:30 AM
        expected_resolution_by = add_to_date(getdate(mock_date), days=4, hours=12)

        self.assertEqual(expected_response_by, ticket.response_by)
        self.assertEqual(expected_resolution_by, ticket.resolution_by)

    def test_response_resolution_with_holdtime(self):
        mock_date = add_to_date(get_current_week_monday(hours=0), days=3, hours=15)

        ticket = make_ticket(
            priority="Urgent", service_level_agreement_creation=mock_date
        )

        expected_response_by = add_to_date(mock_date, minutes=30)  # 30 minutes later
        expected_resolution_by = add_to_date(mock_date, hours=2)  # 2 hours later

        self.assertEqual(expected_response_by, ticket.response_by)
        self.assertEqual(expected_resolution_by, ticket.resolution_by)

        ticket.reload()
        ticket.status = "Replied"
        ticket.save()

        ticket.reload()
        ticket.total_hold_time = 3600  # 1 hour hold time
        ticket.save()

        ticket = ticket.reload()
        new_expected_resolution_by = add_to_date(expected_resolution_by, hours=1)

        self.assertEqual(new_expected_resolution_by, ticket.resolution_by)

        ticket.total_hold_time = 3601  # 1 hour + 1 second, hold time
        ticket.save()
        ticket = ticket.reload()

        new_expected_resolution_by = add_to_date(
            getdate(expected_resolution_by), days=1, hours=10, seconds=1
        )
        self.assertEqual(new_expected_resolution_by, ticket.resolution_by)

    def tearDown(self):
        # Clean up after tests
        remove_holidays()
