# Copyright (c) 2023, Frappe Technologies and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_to_date, get_datetime, getdate

from helpdesk.test_utils import (
    add_holiday,
    get_current_week_monday,
    get_priority_response_resolution_time,
    make_status,
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
    def setUp(self):
        frappe.db.delete("HD Ticket")
        frappe.get_doc(
            {"doctype": "User", "first_name": "Non Agent", "email": non_agent}
        ).insert(ignore_if_duplicate=True)

        frappe.get_doc(
            {"doctype": "User", "first_name": "Agent", "email": agent}
        ).insert(ignore_if_duplicate=True)
        frappe.get_doc({"doctype": "HD Agent", "user": agent}).insert(
            ignore_if_duplicate=True
        )

        frappe.get_doc(
            {"doctype": "User", "first_name": "Agent2", "email": agent2}
        ).insert(ignore_if_duplicate=True)
        frappe.get_doc({"doctype": "HD Agent", "user": agent2}).insert(
            ignore_if_duplicate=True
        )

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

    def test_sla_status(self):
        ticket = make_ticket(
            priority="Urgent",
        )
        self.assertEqual(ticket.agreement_status, "First Response Due")

        ticket.reload()
        ticket.status = "Replied"
        ticket.save()
        self.assertEqual(ticket.agreement_status, "Paused")
        # First response fulfilled
        self.assertTrue(ticket.first_responded_on < ticket.response_by)

        ticket.reload()
        ticket.status = "Open"
        ticket.save()
        self.assertEqual(ticket.agreement_status, "Resolution Due")

        ticket.reload()
        ticket.status = "Resolved"
        ticket.save()
        self.assertEqual(ticket.agreement_status, "Fulfilled")

    def test_hold_time_resolution_time(self):
        # Keep the ticket in paused state for 30 minutes to test hold time, resolution_by should increase by 30 minutes
        ticket = None
        date = get_current_week_monday(hours=12)
        with self.freeze_time(date):
            ticket = make_ticket(priority="High")
            self.assertEqual(ticket.agreement_status, "First Response Due")
            self.assertEqual(ticket.response_by, add_to_date(date, hours=1))
            self.assertEqual(ticket.resolution_by, add_to_date(date, hours=4))

        ticket.reload()
        with self.freeze_time(add_to_date(date, minutes=30)):
            ticket.status = "Replied"
            ticket.save()
            self.assertEqual(ticket.first_responded_on, get_datetime())
            self.assertEqual(ticket.agreement_status, "Paused")

        ticket.reload()
        with self.freeze_time(add_to_date(date, hours=1)):
            ticket.status = "Open"
            ticket.save()
            ticket.reload()

            self.assertEqual(ticket.agreement_status, "Resolution Due")
            self.assertEqual(
                ticket.resolution_by, add_to_date(date, hours=4, minutes=30)
            )

        ticket.reload()
        with self.freeze_time(add_to_date(date, hours=1, minutes=30)):
            ticket.status = "Resolved"
            ticket.save()
            ticket = ticket.reload()

            self.assertEqual(ticket.agreement_status, "Fulfilled")
            # Resolution time should be 1 hour more than the original resolution time
            self.assertEqual(ticket.resolution_time, 60 * 60)

    def test_hold_time_resolution_time_with_holiday(self):
        # create friday as holiday
        # create ticket on thursday 5:30 PM with high priority
        # change status to replied on 5:50 PM
        # change status to open on 12:30 PM on Monday
        # total_hold_time should be 1 hour 40 minutes
        # change status to resolved on 13:00 PM on Monday
        # resolution time should be 3 hours 30 minutes
        add_holiday(
            getdate(add_to_date(get_current_week_monday(), days=4)),
            "Test Holiday",
        )
        ticket = None
        date = add_to_date(
            get_current_week_monday(hours=0), days=3, hours=17, minutes=30
        )
        with self.freeze_time(date):
            ticket = make_ticket(priority="High")
            ticket.reload()

        with self.freeze_time(add_to_date(date, minutes=20)):
            ticket.status = "Replied"
            ticket.save()
            self.assertEqual(ticket.first_responded_on, get_datetime())
            self.assertEqual(ticket.agreement_status, "Paused")

        ticket.reload()
        next_monday_date = add_to_date(
            get_current_week_monday(hours=0), days=7, hours=12, minutes=30
        )
        with self.freeze_time(next_monday_date):
            ticket.status = "Open"
            ticket.save()
            ticket = ticket.reload()

            self.assertEqual(ticket.agreement_status, "Resolution Due")
            # total hold time should be 10 minutes from 5:50 PM to 6:00 PM on Thursday
            #  + 10 to 12:30 pm on monday
            expected_hold_time = 10 * 60 + 150 * 60
            self.assertEqual(ticket.total_hold_time, expected_hold_time)

        ticket.reload()
        with self.freeze_time(add_to_date(next_monday_date, minutes=30)):

            ticket.status = "Resolved"
            ticket.save()
            ticket = ticket.reload()

            self.assertEqual(ticket.agreement_status, "Fulfilled")
            # Resolution time should be 1 hour more than the original resolution time
            expected_total_time_to_resolve = (60 * 60 * 3) + 30 * 60
            expected_resolution_time = (
                expected_total_time_to_resolve - ticket.total_hold_time
            )
            self.assertEqual(
                ticket.resolution_time, expected_resolution_time
            )  # 3 hours 30 minutes

    def test_default_status(self):
        # create a new status
        # go to hd settings and set it as default
        # create a new ticket, it should have the new status as default
        ticket = make_ticket()
        self.assertNotEqual(ticket.status, "New")

        status = make_status(name="New")
        frappe.db.set_single_value("HD Settings", "default_ticket_status", status.name)
        ticket2 = make_ticket()
        self.assertEqual(ticket2.status, status.name)

        ticket2.reload()
        ticket2.status = "Replied"
        ticket2.save()
        self.assertEqual(ticket2.status, "Replied")

        ticket2.reload()

        ticket2.create_communication_via_contact("Testing reply")
        ticket2.reload()
        # reopen the ticket

        # status remains default one unless agent replies
        self.assertEqual(ticket2.status, "New")

    def test_hold_time_resolution_time_with_holiday_with_custom_status(self):
        """
        same test case as test_hold_time_resolution_time_with_holiday
        but with custom statuses

        """
        add_holiday(
            getdate(add_to_date(get_current_week_monday(), days=4)),
            "Test Holiday",
        )
        paused_status = make_status(name="On Hold", category="Paused")
        resolved_status = make_status(name="Completed", category="Resolved")
        ticket = None
        date = add_to_date(
            get_current_week_monday(hours=0), days=3, hours=17, minutes=30
        )
        with self.freeze_time(date):
            ticket = make_ticket(priority="High")
            ticket.reload()

        with self.freeze_time(add_to_date(date, minutes=20)):
            ticket.status = paused_status.name
            ticket.save()
            self.assertEqual(ticket.first_responded_on, get_datetime())
            self.assertEqual(ticket.agreement_status, "Paused")

        ticket.reload()

        next_monday_date = add_to_date(
            get_current_week_monday(hours=0), days=7, hours=12, minutes=30
        )
        with self.freeze_time(next_monday_date):
            ticket.status = "Open"
            ticket.save()
            ticket = ticket.reload()

            self.assertEqual(ticket.agreement_status, "Resolution Due")
            # total hold time should be 10 minutes from 5:50 PM to 6:00 PM on Thursday
            #  + 10 to 12:30 pm on monday
            expected_hold_time = 10 * 60 + 150 * 60
            self.assertEqual(ticket.total_hold_time, expected_hold_time)

        ticket.reload()

        with self.freeze_time(add_to_date(next_monday_date, minutes=30)):
            ticket.status = resolved_status.name
            ticket.save()
            ticket = ticket.reload()

            self.assertEqual(ticket.agreement_status, "Fulfilled")
            # Resolution time should be 1 hour more than the original resolution time
            expected_total_time_to_resolve = (60 * 60 * 3) + 30 * 60
            expected_resolution_time = (
                expected_total_time_to_resolve - ticket.total_hold_time
            )
            self.assertEqual(ticket.resolution_time, expected_resolution_time)

    def test_resolve_closed_resolution_time(self):
        """
        Ticket resolution time should not change if ticket goes from resolved to closed
        """
        date = get_current_week_monday(hours=12)
        with self.freeze_time(date):
            ticket = make_ticket(priority="High")

        ticket.reload()
        with self.freeze_time(add_to_date(date, minutes=30)):
            ticket.status = "Resolved"
            ticket.save()
            self.assertEqual(ticket.resolution_time, 30 * 60)

        ticket.reload()
        with self.freeze_time(add_to_date(date, days=1)):
            ticket.status = "Closed"
            ticket.save()
            self.assertEqual(ticket.resolution_time, 30 * 60)

    def tearDown(self):
        remove_holidays()
        frappe.db.set_single_value("HD Settings", "default_ticket_status", "Open")
        frappe.delete_doc("HD Ticket Status", "New", force=True)
