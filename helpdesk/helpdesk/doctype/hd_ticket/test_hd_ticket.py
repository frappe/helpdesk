# Copyright (c) 2023, Frappe Technologies and Contributors
# See license.txt

from datetime import timedelta
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_to_date, get_datetime, getdate, now_datetime

from helpdesk.api.ticket import bulk_reply
from helpdesk.consts import DEFAULT_SLA
from helpdesk.helpdesk.doctype.hd_ticket.api import (
    merge_ticket,
    show_outside_hours_banner,
    split_ticket,
)
from helpdesk.helpdesk.doctype.hd_ticket.hd_ticket import (
    close_tickets_after_n_days,
    has_permission,
    permission_query,
)
from helpdesk.test_utils import (
    SLA_PRIORITY_NAME,
    add_comment,
    add_contact_in_customer,
    add_holiday,
    create_contact,
    create_customer,
    get_current_week_monday,
    get_latest_ticket_communication,
    get_priority_response_resolution_time,
    make_priority,
    make_sla,
    make_status,
    make_team,
    make_ticket,
    remove_holidays,
    set_ticket_status_and_communication_date,
    update_role_in_customer,
    upload_test_file,
)

ERROR_MSG_RESPONSE = "Response time differs by more than 1 second"
ERROR_MSG_RESOLUTION = "Resolution time differs by more than 1 second"

SLA_DOCTYPE = "HD Service Level Agreement"
UNINCLUDED_PRIORITY = "Critical"  # deliberately absent from every SLA's priorities


def set_default_sla(name: str, value: int):
    """Tick or untick a policy as the Default SLA, through the controller."""
    sla = frappe.get_doc(SLA_DOCTYPE, name)
    sla.default_sla = value
    sla.save()


def get_ticket_obj():
    return {
        "doctype": "HD Ticket",
        "subject": "Test Ticket",
        "description": "Test Ticket Description",
    }


def sent_replies(ticket_name: str):
    """Agent replies saved on a ticket, oldest first."""
    return frappe.get_all(
        "Communication",
        filters={
            "reference_doctype": "HD Ticket",
            "reference_name": ticket_name,
            "sent_or_received": "Sent",
        },
        fields=["name", "message_id", "in_reply_to"],
        order_by="creation asc",
    )


non_agent = "non_agent@test.com"
agent = "agent@test.com"
agent2 = "agent2@test.com"


CONTACTS = [
    "testc1@example.com",
    "testc2@example.com",
    "testc3@example.com",
    "testc4@example.com",
]
CUSTOMERS = ["Test Org 1", "Test Org 2"]


class TestHDTicket(IntegrationTestCase):
    def setUp(self):
        frappe.db.delete("HD Ticket")
        frappe.get_doc(
            {"doctype": "User", "first_name": "Non Agent", "email": non_agent}
        ).insert(ignore_if_duplicate=True)

        frappe.get_doc(
            {"doctype": "User", "first_name": "Agent", "email": agent}
        ).insert(ignore_if_duplicate=True)

        frappe.get_doc(
            {"doctype": "HD Agent", "user": agent, "agent_name": "agent"}
        ).insert(ignore_if_duplicate=True)

        frappe.get_doc(
            {"doctype": "User", "first_name": "Agent2", "email": agent2}
        ).insert(ignore_if_duplicate=True)
        frappe.get_doc(
            {"doctype": "HD Agent", "user": agent2, "agent_name": "agent2"}
        ).insert(ignore_if_duplicate=True)
        frappe.set_value("HD Settings", "HD Settings", "enable_outside_hours_banner", 1)

    def test_ticket_creation(self):
        ticket = frappe.get_doc(get_ticket_obj())
        ticket.insert()
        self.assertTrue(ticket.name)

    def test_update_perms_skipped_without_a_previous_version(self):
        # a before_insert hook that persists the ticket clears __islocal, so is_new()
        # can be False on create while there is still no previous version to check
        frappe.set_user(non_agent)
        ticket = frappe.get_doc({**get_ticket_obj(), "via_customer_portal": 1})
        ticket.set("__islocal", False)
        ticket.check_update_perms()
        frappe.set_user("Administrator")

    def test_parse_content_strips_html_comments(self):
        ticket = frappe.get_doc(get_ticket_obj())
        ticket.insert()
        content = (
            "<blockquote><!--[if !mso]><!--><!--<![endif]-->"
            "<!--[if gte mso 9]><xml><o:shapedefaults/></xml><![endif]-->"
            "<p>Dear Admin,</p></blockquote>"
        )
        parsed = ticket.parse_content(content)
        self.assertNotIn("<!--", parsed)
        self.assertIn("<p>Dear Admin,</p>", parsed)

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
            DEFAULT_SLA, "High", ticket_creation, add_to_time=False
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

    def test_ticket_merge(self):
        ticket1 = make_ticket(description="Test Desc 1")
        add_comment(ticket1.name, "First comment on ticket 1")

        ticket2 = make_ticket(description="Test Desc 2")
        add_comment(ticket2.name, "First comment on ticket 2")

        merge_ticket(source=ticket1.name, target=ticket2.name)
        ticket1.reload()
        self.assertEqual(ticket1.status, "Closed")
        self.assertTrue(ticket1.is_merged)
        self.assertEqual(ticket1.merged_with, ticket2.name)

        ticket2.reload()
        comments = frappe.get_all(
            "HD Ticket Comment",
            filters={
                "reference_ticket": ticket2.name,
            },
            fields=["content", "name"],
        )
        self.assertEqual(
            len(comments), 3
        )  # 2 original comments + 1 merge comment (Ticket 1 merged into Ticket 2)

    def test_reply_to_merged_ticket_redirects_to_target(self):
        source = make_ticket(description="Merged source")
        target = make_ticket(description="Merge target")

        merge_ticket(source=source.name, target=target.name)
        source.reload()
        self.assertTrue(source.is_merged)
        self.assertEqual(source.status, "Closed")

        # An incoming reply lands on the merged source ticket.
        communication = frappe.get_doc(
            {
                "doctype": "Communication",
                "communication_type": "Communication",
                "communication_medium": "Email",
                "sent_or_received": "Received",
                "subject": f"Re: {source.subject}",
                "content": "Customer reply to merged ticket",
                "reference_doctype": "HD Ticket",
                "reference_name": source.name,
            }
        ).insert(ignore_permissions=True)

        # The merged source must stay closed and merged.
        source.reload()
        self.assertEqual(source.status, "Closed")
        self.assertTrue(source.is_merged)

        # The communication is redirected to the target ticket.
        self.assertEqual(
            frappe.db.get_value("Communication", communication.name, "reference_name"),
            target.name,
        )

    def test_merge_cycle_does_not_resolve_target(self):
        # A corrupt cycle (A merged into B, B merged back into A) must not redirect a reply
        # onto another merged ticket, which would recurse until the request fails.
        ticket_a = make_ticket(description="Cycle A")
        ticket_b = make_ticket(description="Cycle B")

        merge_ticket(source=ticket_a.name, target=ticket_b.name)
        ticket_b.reload()
        ticket_b.db_set("is_merged", 1)
        ticket_b.db_set("merged_with", ticket_a.name)

        ticket_a.reload()
        self.assertIsNone(ticket_a.get_merge_target())

    def test_reply_on_unresolvable_merge_is_not_dropped(self):
        # No safe merge target (corrupt cycle): the reply must be handled here, not dropped.
        ticket_a = make_ticket(description="Cycle A")
        ticket_b = make_ticket(description="Cycle B")

        merge_ticket(source=ticket_a.name, target=ticket_b.name)
        ticket_b.reload()
        ticket_b.db_set("is_merged", 1)
        ticket_b.db_set("merged_with", ticket_a.name)

        communication = frappe.get_doc(
            {
                "doctype": "Communication",
                "communication_type": "Communication",
                "communication_medium": "Email",
                "sent_or_received": "Received",
                "subject": f"Re: {ticket_a.subject}",
                "content": "Customer reply on cyclic merge",
                "reference_doctype": "HD Ticket",
                "reference_name": ticket_a.name,
            }
        ).insert(ignore_permissions=True)

        # The reply stays on this ticket (not redirected) and is handled here.
        self.assertEqual(
            frappe.db.get_value("Communication", communication.name, "reference_name"),
            ticket_a.name,
        )
        ticket_a.reload()
        self.assertIsNotNone(ticket_a.last_customer_response)

    def test_ticket_split(self):
        ticket1 = make_ticket(description="Test Desc for split")

        ticket1.reply_via_agent(message="Test reply to split")
        communcation_name = frappe.get_all(
            "Communication",
            filters={
                "reference_doctype": "HD Ticket",
                "reference_name": ticket1.name,
            },
            pluck="name",
        )[0]
        self.assertTrue(communcation_name)

        ticket2: str = split_ticket(
            subject="Split Ticket", communication_id=communcation_name
        )
        ticket2_doc = frappe.get_doc("HD Ticket", ticket2)
        self.assertTrue(ticket2_doc)
        self.assertEqual(ticket2_doc.subject, "Split Ticket")
        self.assertTrue(
            frappe.get_value("Communication", communcation_name, "reference_name"),
            ticket2_doc.name,
        )

    def test_parse_content_embeds_site_files_only(self):
        """
        Site file images must swap src for embed (so the framework inlines them
        as cid attachments), while external and data URIs keep their src.
        """
        ticket = make_ticket()

        parsed = ticket.parse_content('<img src="/private/files/shot.png">')
        self.assertIn('embed="/private/files/shot.png"', parsed)
        self.assertNotIn("src=", parsed)

        parsed = ticket.parse_content('<img src="/files/public.png">')
        self.assertIn('embed="/files/public.png"', parsed)
        self.assertNotIn("src=", parsed)

        external = '<img src="https://example.com/logo.png"/>'
        self.assertEqual(ticket.parse_content(external), external)

        data_uri = '<img src="data:image/png;base64,AAA"/>'
        self.assertEqual(ticket.parse_content(data_uri), data_uri)

        self.assertEqual(ticket.parse_content(""), "")

    def test_ticket_inside_working_hours(self):
        inside_working_hour = get_current_week_monday(hours=14)
        with self.freeze_time(inside_working_hour):
            ticket = make_ticket(priority="High")
            self.assertFalse(ticket.raised_outside_working_hours)

    def test_ticket_inside_working_hours_currently_outside(self):
        inside_working_hour = get_current_week_monday(hours=14)
        with self.freeze_time(inside_working_hour):
            # Ticket created inside working hours
            ticket = make_ticket(priority="High")
            self.assertFalse(ticket.raised_outside_working_hours)
            banner_shown = show_outside_hours_banner(ticket.name)["show"]
            self.assertFalse(banner_shown)

        ticket.reload()
        with self.freeze_time(get_current_week_monday(hours=20)):
            banner_shown = show_outside_hours_banner(ticket.name)["show"]
            self.assertFalse(banner_shown)

    def test_ticket_outside_working_hours(self):
        outside_working_hour = get_current_week_monday(hours=8)
        with self.freeze_time(outside_working_hour):
            ticket = make_ticket(priority="High")
            banner_shown = show_outside_hours_banner(ticket.name)["show"]
            self.assertTrue(ticket.raised_outside_working_hours)
            self.assertTrue(banner_shown)

    def test_ticket_outside_working_hours_currently_in_working_hour(self):
        outside_working_hours = get_current_week_monday(hours=8)
        with self.freeze_time(outside_working_hours):
            ticket = make_ticket(priority="High")
            banner_shown = show_outside_hours_banner(ticket.name)["show"]
            self.assertTrue(ticket.raised_outside_working_hours)
            self.assertTrue(banner_shown)

        ticket.reload()
        newtime = add_to_date(get_current_week_monday(hours=14), days=1)
        with self.freeze_time(newtime):
            banner_shown = show_outside_hours_banner(ticket.name)["show"]
            self.assertFalse(banner_shown)
            self.assertTrue(ticket.raised_outside_working_hours)

    def test_ticket_outside_working_hours_weekend(self):
        weekend = add_to_date(get_current_week_monday(), days=5, hours=14)
        with self.freeze_time(weekend):
            ticket = make_ticket(priority="High")
            banner_shown = show_outside_hours_banner(ticket.name)["show"]
            self.assertTrue(ticket.raised_outside_working_hours)
            self.assertTrue(banner_shown)

    def test_ticket_outside_working_hours_agent_replied(self):
        outside_working_hour = get_current_week_monday(hours=8)
        with self.freeze_time(outside_working_hour):
            ticket = make_ticket(priority="High")
            ticket.reply_via_agent(message="Test reply to split")
            banner_shown = show_outside_hours_banner(ticket.name)["show"]
            self.assertTrue(ticket.raised_outside_working_hours)
            self.assertFalse(banner_shown)

    def test_if_banner_not_shown_after_next_working_day(self):
        outside_working_hour_day_1 = get_current_week_monday(hours=20)
        with self.freeze_time(outside_working_hour_day_1):
            ticket = make_ticket(priority="low")

        ticket.reload()
        next_working_day = add_to_date(get_current_week_monday(hours=20), days=1)
        with self.freeze_time(next_working_day):
            banner_shown = show_outside_hours_banner(ticket.name)["show"]
            self.assertFalse(banner_shown)

    def test_contact_ticket_visibility(self):
        """
        Test case to validate that contact can only see the tickets raised by them only.
        If part of any org still should only see the tickets raised by them and not the tickets raised by other contacts of the same org. It should also set the customer of the ticket as the org to which contact belongs to.
        """
        user_contact = create_contact("Test C1", CONTACTS[0])
        user = user_contact.get("user", "")
        frappe.set_user(user)
        tickets = frappe.get_list("HD Ticket", filters={"owner": user}, pluck="name")
        self.assertEqual(len(tickets), 0)

        make_ticket()
        tickets = frappe.get_list("HD Ticket", filters={"owner": user}, pluck="name")
        self.assertEqual(len(tickets), 1)

    def test_ticket_visibility_within_customer(self):
        """
        Test case to validate ticket visibility for contacts linked with same customer
        Checks:
            - Contact linked with same customer should be able to raise ticket for that customer
            - Contact should only see the tickets raised by them if they are not HD Customer Manager
            - If contact is made manager, they should see all the tickets of the customer
        """
        user_contact1 = create_contact("Test C1", CONTACTS[0])
        user_contact2 = create_contact("Test C2", CONTACTS[1])
        contacts = [
            {"contact_name": user_contact1.get("contact")},
            {"contact_name": user_contact2.get("contact")},
        ]
        customer = create_customer(CUSTOMERS[0], contacts)

        frappe.set_user(user_contact1.get("user"))
        ticket1 = make_ticket()

        frappe.set_user(user_contact2.get("user"))
        ticket2 = make_ticket()

        frappe.set_user(user_contact1.get("user"))
        ticket3 = make_ticket()
        user1_tickets = frappe.get_list("HD Ticket", fields=["name", "customer"])

        self.assertEqual(
            set([ticket["name"] for ticket in user1_tickets]),
            set([ticket1.name, ticket3.name]),
        )
        for ticket in user1_tickets:
            self.assertEqual(
                ticket["customer"],
                customer.name,
                "Customer should be set as {0}, but got {1}".format(
                    customer.name, ticket["customer"]
                ),
            )

        frappe.set_user(user_contact2.get("user", ""))
        user2_tickets = frappe.get_list("HD Ticket", pluck="name")
        self.assertEqual(
            set(user2_tickets),
            set([ticket2.name]),
            "User should only see the tickets raised by them if they are not HD Customer Manager",
        )

        frappe.set_user("Administrator")
        customer.reload()
        update_role_in_customer(
            customer, user_contact2.get("contact"), "HD Customer Manager", True
        )

        frappe.set_user(user_contact2.get("user", ""))
        user2_manager_tickets = frappe.get_list("HD Ticket", pluck="name")
        self.assertEqual(
            set(user2_manager_tickets),
            set([ticket1.name, ticket2.name, ticket3.name]),
            "Manager should see all the tickets of the customer",
        )

    def test_contact_ticket_visibility_in_multiple_org(self):
        """
        Test case to validate ticket visibility for contacts linked with multiple customers
        Checks:
            - Contact linked with multiple customers should be able to raise ticket for both customers
            - Contact should only see the tickets raised by them even if they are linked with multiple customers
            - If contact is made manager in one org, they should only see the tickets of that org where they are manager and the tickets raised by them in other org, but not the tickets of other org where they are not manager
            - Customer of the ticket should be set as the org for which ticket is raised, even if contact is linked with multiple orgs
        """
        user_contact1 = create_contact("Test C1", CONTACTS[0])
        user_contact2 = create_contact("Test C2", CONTACTS[1])
        user_contact3 = create_contact("Test C3", CONTACTS[2])
        contacts_org1 = [
            {"contact_name": user_contact1.get("contact")},
            {"contact_name": user_contact2.get("contact")},
        ]
        contacts_org2 = [
            {"contact_name": user_contact2.get("contact")},
            {"contact_name": user_contact3.get("contact")},
        ]
        customer1 = create_customer(CUSTOMERS[0], contacts_org1)
        customer2 = create_customer(CUSTOMERS[1], contacts_org2)

        frappe.set_user(user_contact1.get("user"))
        contact1_ticket1 = make_ticket()
        self.assertEqual(contact1_ticket1.customer, customer1.name)

        frappe.set_user(user_contact2.get("user"))
        contact2_ticket1 = make_ticket(save=False, via_customer_portal=True)
        self.assertRaises(frappe.ValidationError, contact2_ticket1.save)  # throws error
        # adds customer explicitly and saves
        contact2_ticket1.customer = customer1.name
        contact2_ticket1.save()
        self.assertEqual(contact2_ticket1.customer, customer1.name)

        contact2_ticket2 = make_ticket(customer=customer2.name)
        self.assertEqual(contact2_ticket2.customer, customer2.name)

        user2_tickets = frappe.get_list("HD Ticket", fields=["name", "customer"])
        self.assertEqual(
            set([ticket["name"] for ticket in user2_tickets]),
            set([contact2_ticket1.name, contact2_ticket2.name]),
            "User should only see the tickets raised by them",
        )

        frappe.set_user(user_contact1.get("user", ""))
        user1_tickets = frappe.get_list("HD Ticket", fields=["name", "customer"])
        self.assertEqual(
            set([ticket["name"] for ticket in user1_tickets]),
            set([contact1_ticket1.name]),
            "User should only see the tickets raised by them",
        )
        for ticket in user1_tickets:
            self.assertEqual(
                ticket["customer"],
                customer1.name,
                "Customer should be set as {0}, but got {1}".format(
                    customer1.name, ticket["customer"]
                ),
            )

        frappe.set_user(user_contact3.get("user", ""))
        contact3_ticket1 = make_ticket()
        self.assertEqual(contact3_ticket1.customer, customer2.name)
        contact3_tickets = frappe.get_list("HD Ticket", fields=["name", "customer"])
        self.assertEqual(
            set([ticket["name"] for ticket in contact3_tickets]),
            set([contact3_ticket1.name]),
            "User should only see the tickets raised by them",
        )

        update_role_in_customer(
            customer1, user_contact1.get("contact"), "HD Customer Manager", True
        )
        frappe.set_user(user_contact1.get("user", ""))
        user1_manager_tickets = frappe.get_list("HD Ticket", pluck="name")
        self.assertEqual(
            set(user1_manager_tickets),
            set([contact1_ticket1.name, contact2_ticket1.name]),
            "Manager should see all the tickets of the customer",
        )
        frappe.set_user(user_contact2.get("user", ""))
        user2_tickets = frappe.get_list("HD Ticket", pluck="name")
        self.assertEqual(
            set(user2_tickets),
            set(
                [
                    contact2_ticket1.name,
                    contact2_ticket2.name,
                ]
            ),
            "User should only see the tickets raised by them",
        )

        update_role_in_customer(
            customer2, user_contact2.get("contact"), "HD Customer Manager", True
        )

        frappe.set_user(user_contact2.get("user", ""))
        user2_manager_tickets = frappe.get_list("HD Ticket", pluck="name")
        self.assertEqual(
            set(user2_manager_tickets),
            set(
                [
                    contact2_ticket1.name,
                    contact2_ticket2.name,
                    contact3_ticket1.name,
                ]
            ),
            "Manager should see all the tickets of the customer where they are manager and also the tickets raised by them",
        )

        frappe.set_user(user_contact1.get("user", ""))
        user1_manager_tickets = frappe.get_list("HD Ticket", pluck="name")
        self.assertEqual(
            set(user1_manager_tickets),
            set([contact1_ticket1.name, contact2_ticket1.name]),
            "Manager should see all the tickets of the customer where they are manager and also the tickets raised by them",
        )

        frappe.set_user("Administrator")
        user_contact4 = create_contact("Test C4", CONTACTS[3])
        add_contact_in_customer(customer1, user_contact4.get("contact"), True, True)
        update_role_in_customer(
            customer1, user_contact1.get("contact"), "HD Customer", False
        )

        frappe.set_user(user_contact1.get("user", ""))
        user1_tickets = frappe.get_list("HD Ticket", fields=["name", "customer"])
        self.assertEqual(
            set([ticket["name"] for ticket in user1_tickets]),
            set([contact1_ticket1.name]),
            "User should only see the tickets raised by them",
        )
        for ticket in user1_tickets:
            self.assertEqual(
                ticket["customer"],
                customer1.name,
                "Customer should be set as {0}, but got {1}".format(
                    customer1.name, ticket["customer"]
                ),
            )

        frappe.set_user(user_contact4.get("user", ""))
        user4_tickets = frappe.get_list("HD Ticket", fields=["name", "customer"])
        self.assertEqual(
            set([ticket["name"] for ticket in user4_tickets]),
            set([contact1_ticket1.name, contact2_ticket1.name]),
            "User should see all the tickets of the customer where they are added as contact",
        )
        for ticket in user4_tickets:
            self.assertEqual(
                ticket["customer"],
                customer1.name,
                "Customer should be set as {0}, but got {1}".format(
                    customer1.name, ticket["customer"]
                ),
            )

    def test_contact_invalid_customer_ticket(self):
        # a contact should not be able to raise ticket for a customer they are not part of
        user_contact1 = create_contact("Test C1", CONTACTS[0])
        customer1 = create_customer(
            CUSTOMERS[0], [{"contact_name": user_contact1.get("contact")}]
        )
        customer2 = create_customer(CUSTOMERS[1], [])
        frappe.set_user(user_contact1.get("user"))
        contact1_ticket1 = make_ticket(customer=customer1.name)
        self.assertEqual(contact1_ticket1.customer, customer1.name)
        contact1_ticket2 = make_ticket(customer=customer2.name, save=False)
        self.assertRaises(frappe.ValidationError, contact1_ticket2.save)

    def test_reply_via_agent_with_only_cc(self):
        """
        reply_via_agent should succeed when only cc is provided and to is empty/None
        """
        ticket = make_ticket()
        cc_recipient = "cc_only@test.com"
        ticket.reply_via_agent(message="Test reply", cc=cc_recipient)
        communication_doc = get_latest_ticket_communication(ticket.name)
        if hasattr(communication_doc, "to") and communication_doc.to:
            self.assertFalse(communication_doc.to)
        if hasattr(communication_doc, "cc") and communication_doc.cc:
            self.assertEqual(communication_doc.cc, cc_recipient)
        if hasattr(communication_doc, "bcc") and communication_doc.bcc:
            self.assertFalse(communication_doc.bcc)

    def test_reply_via_agent_with_only_bcc(self):
        """
        reply_via_agent should succeed when only bcc is provided and to is empty/None
        """
        ticket = make_ticket()
        bcc_recipient = "bcc_only@test.com"
        ticket.reply_via_agent(message="Test reply", bcc=bcc_recipient)
        communication_doc = get_latest_ticket_communication(ticket.name)
        if hasattr(communication_doc, "to") and communication_doc.to:
            self.assertFalse(communication_doc.to)
        if hasattr(communication_doc, "cc") and communication_doc.cc:
            self.assertFalse(communication_doc.cc)
        if hasattr(communication_doc, "bcc") and communication_doc.bcc:
            self.assertEqual(communication_doc.bcc, bcc_recipient)

    def test_reply_via_agent_with_cc_and_bcc_no_to(self):
        """
        reply_via_agent should succeed when both cc and bcc are provided but to is empty
        """
        ticket = make_ticket()
        cc_recipient = "cc_combo@test.com"
        bcc_recipient = "bcc_combo@test.com"
        ticket.reply_via_agent(message="Test reply", cc=cc_recipient, bcc=bcc_recipient)
        comm = get_latest_ticket_communication(ticket.name)
        communication_doc = get_latest_ticket_communication(ticket.name)
        if hasattr(communication_doc, "to") and communication_doc.to:
            self.assertFalse(communication_doc.to)
        if hasattr(communication_doc, "cc") and communication_doc.cc:
            self.assertEqual(communication_doc.cc, cc_recipient)
        if hasattr(communication_doc, "bcc") and communication_doc.bcc:
            self.assertEqual(communication_doc.bcc, bcc_recipient)

    def test_agent_reply_stores_unique_message_id_and_threads_onto_previous(self):
        """Without this, every agent reply arrives as a new thread."""
        ticket = make_ticket()

        ticket.reply_via_agent(message="First reply", to="customer@test.com")
        first = get_latest_ticket_communication(ticket.name)

        ticket.reload()
        ticket.reply_via_agent(message="Second reply", to="customer@test.com")
        second = get_latest_ticket_communication(ticket.name)

        self.assertTrue(first.message_id, "reply must store its own id")
        self.assertTrue(second.message_id, "reply must store its own id")
        self.assertNotEqual(
            first.message_id, second.message_id, "ids must not be reused"
        )
        self.assertEqual(
            second.in_reply_to, first.name, "second reply follows the first"
        )

    def test_agent_reply_sends_the_message_id_it_stored(self):
        """If we store an id but send a different one, the customer never has the id
        the next reply points at."""
        email_account = frappe.get_doc(
            {
                "doctype": "Email Account",
                "email_account_name": "Threading Test",
                "email_id": "threading-test@example.com",
                "enable_outgoing": 1,
                "smtp_server": "smtp.example.com",
            }
        ).insert(ignore_if_duplicate=True)

        reply_email_enabled = frappe.db.get_single_value(
            "HD Settings", "enable_reply_email_via_agent"
        )
        frappe.db.set_single_value("HD Settings", "enable_reply_email_via_agent", 1)
        try:
            ticket = make_ticket()
            with patch("frappe.sendmail") as sendmail:
                ticket.reply_via_agent(
                    message="Reply",
                    to="customer@test.com",
                    from_email={
                        "email_account": email_account.name,
                        "email_id": email_account.email_id,
                    },
                )
        finally:
            # rollback is per test class, so restore or later tests inherit this
            frappe.db.set_single_value(
                "HD Settings", "enable_reply_email_via_agent", reply_email_enabled
            )

        communication = get_latest_ticket_communication(ticket.name)
        self.assertTrue(sendmail.called, "reply should have been emailed")
        self.assertEqual(
            sendmail.call_args.kwargs.get("message_id"),
            communication.message_id,
            "wire Message-Id must match the one stored on the Communication",
        )

    def test_portal_reply_does_not_break_agent_reply_threading(self):
        """A portal reply sent no email, so replies after it must skip past it."""
        ticket = make_ticket()

        ticket.reply_via_agent(message="First reply", to="customer@test.com")
        first = get_latest_ticket_communication(ticket.name)

        # each of these is its own request in production; replying updates the ticket row
        ticket.reload()
        ticket.create_communication_via_contact(message="Customer portal reply")
        portal = get_latest_ticket_communication(ticket.name)
        self.assertFalse(portal.message_id, "portal replies store no id")

        ticket.reload()
        ticket.reply_via_agent(message="Second reply", to="customer@test.com")
        second = get_latest_ticket_communication(ticket.name)

        self.assertEqual(
            second.in_reply_to, first.name, "follows the last emailed reply"
        )

    def test_agent_replies_thread_on_a_ticket_created_by_email(self):
        """A ticket raised by email: the first reply answers the customer's mail,
        and later replies follow the reply before them."""
        ticket = make_ticket()
        customer_email = frappe.get_doc(
            {
                "doctype": "Communication",
                "communication_type": "Communication",
                "communication_medium": "Email",
                "sent_or_received": "Received",
                "reference_doctype": "HD Ticket",
                "reference_name": ticket.name,
                "subject": f"Re: {ticket.subject}",
                # frappe stores incoming ids without the angle brackets
                "message_id": "customer-mail-1@example.com",
                "content": "my printer is broken",
            }
        ).insert(ignore_permissions=True)

        ticket.reload()
        ticket.reply_via_agent(message="First reply", to="customer@test.com")
        first = get_latest_ticket_communication(ticket.name)

        ticket.reload()
        ticket.reply_via_agent(message="Second reply", to="customer@test.com")
        second = get_latest_ticket_communication(ticket.name)

        self.assertEqual(
            first.in_reply_to, customer_email.name, "first reply answers the customer"
        )
        self.assertEqual(
            second.in_reply_to, first.name, "second reply follows the first"
        )
        self.assertNotEqual(
            first.message_id, second.message_id, "ids must not be reused"
        )

    def test_reply_that_fails_to_send_stores_no_message_id(self):
        """The reply stays visible, but with no id it can never be replied to."""
        ticket = make_ticket()

        with patch("frappe.sendmail", side_effect=Exception("smtp is down")):
            with self.assertRaises(Exception):
                ticket.reply_via_agent(message="Never sent", to="customer@test.com")

        replies = sent_replies(ticket.name)
        self.assertEqual(len(replies), 1, "the attempt stays on the ticket")
        self.assertFalse(replies[0].message_id, "a reply nobody got has no id")

    def test_reply_stores_no_message_id_when_nothing_was_queued(self):
        """sendmail returns nothing when it queued nothing, which is not a send."""
        ticket = make_ticket()

        with patch("frappe.sendmail", return_value=None):
            ticket.reply_via_agent(message="Queued nothing", to="customer@test.com")

        self.assertFalse(get_latest_ticket_communication(ticket.name).message_id)

    def test_next_reply_threads_onto_the_last_one_that_sent(self):
        """The bug this guards: a reply that failed to send must not be answered,
        or the customer gets a reply pointing at an email they never received."""
        ticket = make_ticket()
        real_sendmail = frappe.sendmail

        ticket.reply_via_agent(message="First reply", to="customer@test.com")
        first = get_latest_ticket_communication(ticket.name)

        ticket.reload()
        with patch("frappe.sendmail", side_effect=Exception("smtp is down")):
            with self.assertRaises(Exception):
                ticket.reply_via_agent(
                    message="Second reply, never sent", to="customer@test.com"
                )

        ticket.reload()
        with patch("frappe.sendmail", side_effect=real_sendmail):
            ticket.reply_via_agent(message="Third reply", to="customer@test.com")
        third = get_latest_ticket_communication(ticket.name)

        self.assertTrue(first.message_id, "the first reply did send")
        self.assertEqual(
            third.in_reply_to, first.name, "skips the reply that never went out"
        )

    def test_reply_stores_no_message_id_when_email_is_off(self):
        """No email was sent, so there is no id the customer could ever reply to."""
        previous = frappe.db.get_single_value(
            "HD Settings", "enable_reply_email_via_agent"
        )
        frappe.db.set_single_value("HD Settings", "enable_reply_email_via_agent", 0)
        try:
            ticket = make_ticket()
            ticket.reply_via_agent(message="Not emailed")
            self.assertFalse(get_latest_ticket_communication(ticket.name).message_id)
        finally:
            # rollback is per test class, so restore or later tests inherit this
            frappe.db.set_single_value(
                "HD Settings", "enable_reply_email_via_agent", previous
            )

    def test_security_unauthorized_reply_via_agent(self):
        ticket = make_ticket()
        frappe.set_user(non_agent)

        with self.assertRaises(frappe.PermissionError):
            ticket.reply_via_agent(message="Test unauthorized reply")

        frappe.set_user("Administrator")

    def test_security_unauthorized_assign_agent(self):
        ticket = make_ticket()
        frappe.set_user(non_agent)

        with self.assertRaises(frappe.PermissionError):
            ticket.assign_agent(agent)

        frappe.set_user("Administrator")

    def test_security_info_disclosure_similar_tickets(self):
        from helpdesk.helpdesk.doctype.hd_ticket.api import get_recent_similar_tickets

        ticket = make_ticket()

        frappe.set_user(non_agent)

        with self.assertRaises(frappe.PermissionError):
            get_recent_similar_tickets(ticket.name)

        frappe.set_user("Administrator")
        # clean up any HD Customers left by customer-visibility tests
        for customer in CUSTOMERS:
            frappe.delete_doc("HD Customer", customer, force=True)
        # clean up contacts created by visibility tests
        for email in CONTACTS:
            for c in frappe.db.get_all(
                "Contact", filters={"email_id": email}, pluck="name"
            ):
                frappe.delete_doc("Contact", c, force=True)
            if frappe.db.exists("User", email):
                frappe.delete_doc("User", email, force=True)

    def test_ticket_priority(self):
        # if priority is set, ticket will have the applied priority
        ticket1 = make_ticket(priority="High")
        self.assertEqual(ticket1.priority, "High")

        # if ticket type is set, and ticket type has a priority, the ticket's priority will be the same as type's priority
        ticket_type = frappe.get_doc("HD Ticket Type", "Bug")
        ticket_type.priority = "High"
        ticket_type.save()
        ticket2 = make_ticket(ticket_type="Bug")
        self.assertEqual(ticket2.priority, "High")

        # if ticket type and priority is set, applied priority is given preference
        ticket3 = make_ticket(priority="Low", ticket_type="Bug")
        self.assertEqual(ticket3.priority, "Low")

        # if ticket type is set, and ticket type does not has a priority, the ticket's priority will be the same as applied sla's default priority
        sla_doc = frappe.get_doc("HD Service Level Agreement", DEFAULT_SLA)
        for p in sla_doc.priorities:
            if p.priority == "Low":
                p.default_priority = 1
            else:
                p.default_priority = 0
        sla_doc.save()

        ticket4 = make_ticket(ticket_type="Incident")  # type with no priority
        self.assertEqual(
            ticket4.priority, "Low"
        )  # applied SLA's default priority is assigned

        # ticket created without any type or priority should pick up priority from applied SLA's default
        ticket5 = make_ticket()
        self.assertEqual(ticket5.priority, "Low")

    # Test cases for agreement_status field which is computed based on response_by, resolution_by, first_responded_on, on_hold_since and resolution_date fields
    # In total there are 7 scenarios for agreement_status which are covered in the below test cases:
    def test_agreement_status_first_response_failed(self):
        # Case 1: No reply before response_by (T+30min) → Failed
        # At T+1h, response_by (T+30min) < now (T+1h) → first response failed
        # resolution_by (T+2h) > now (T+1h) → resolution not yet failed
        # is_failed = True → "Failed"
        date = get_current_week_monday(hours=10)
        with self.freeze_time(date):
            ticket = make_ticket(priority="Urgent")

        with self.freeze_time(add_to_date(date, hours=1)):
            ticket.reload()
            ticket.save()
            self.assertEqual(ticket.agreement_status, "Failed")

    def test_agreement_status_resolution_failed(self):
        # Case 2: First response in time, resolution misses deadline → Failed
        #
        # Timeline (Urgent: response_by=T+30min, resolution_by=T+2h):
        #   T+10min  → Replied (Paused): first_responded_on set, on_hold_since=T+10min
        #   T+20min  → Open: off hold, hold_time=10min(600s),
        #              new resolution_by = T + 2h + 10min = T+2h10min
        #   T+2h15min → save: resolution_by (T+2h10min) < now (T+2h15min) → Failed
        date = get_current_week_monday(hours=10)
        with self.freeze_time(date):
            ticket = make_ticket(priority="Urgent")

        with self.freeze_time(add_to_date(date, minutes=10)):
            ticket.reload()
            ticket.status = "Replied"
            ticket.save()

        with self.freeze_time(add_to_date(date, minutes=20)):
            ticket.reload()
            ticket.status = "Open"
            ticket.save()
            self.assertEqual(ticket.agreement_status, "Resolution Due")

        # Re-save past the extended resolution_by (T+2h10min) without changing status
        with self.freeze_time(add_to_date(date, hours=2, minutes=15)):
            ticket.reload()
            ticket.save()
            self.assertEqual(ticket.agreement_status, "Failed")

    def test_agreement_status_both_failed(self):
        # Case 3: No reply given, past both response_by (T+30min) and resolution_by (T+2h)
        # At T+3h: response_by < now AND resolution_by < now → is_failed = True → "Failed"
        date = get_current_week_monday(hours=10)
        with self.freeze_time(date):
            ticket = make_ticket(priority="Urgent")

        with self.freeze_time(add_to_date(date, hours=3)):
            ticket.reload()
            ticket.save()
            self.assertEqual(ticket.agreement_status, "Failed")

    def test_agreement_status_resolution_due_on_hold(self):
        # Case 4: First response given, resolution due, ticket on hold → Paused
        # "Replied" is a Paused-category status — sets first_responded_on AND on_hold_since
        date = get_current_week_monday(hours=10)
        with self.freeze_time(date):
            ticket = make_ticket(priority="Urgent")

        with self.freeze_time(add_to_date(date, minutes=10)):
            ticket.reload()
            ticket.status = "Replied"
            ticket.save()
            self.assertTrue(ticket.first_responded_on)
            self.assertTrue(ticket.on_hold_since)
            self.assertIsNone(ticket.resolution_date)
            self.assertEqual(ticket.agreement_status, "Paused")

    def test_agreement_status_first_response_due(self):
        # Case 5: Fresh ticket — no reply, not on hold → First Response Due
        date = get_current_week_monday(hours=10)
        with self.freeze_time(date):
            ticket = make_ticket(priority="Urgent")
            self.assertIsNone(ticket.first_responded_on)
            self.assertIsNone(ticket.on_hold_since)
            self.assertEqual(ticket.agreement_status, "First Response Due")

    def test_agreement_status_resolution_due(self):
        # Case 6: First response given, came off hold, resolution still pending → Resolution Due
        #
        # Timeline:
        #   T+10min → Replied (Paused): first_responded_on set, on_hold_since set
        #   T+20min → Open: off hold, hold_time=10min, resolution_by extended to T+2h10min
        #   At T+20min: first_responded_on set, on_hold_since=None,
        #               resolution_date=None, now < resolution_by → Resolution Due
        date = get_current_week_monday(hours=10)
        with self.freeze_time(date):
            ticket = make_ticket(priority="Urgent")

        with self.freeze_time(add_to_date(date, minutes=10)):
            ticket.reload()
            ticket.status = "Replied"
            ticket.save()

        with self.freeze_time(add_to_date(date, minutes=20)):
            ticket.reload()
            ticket.status = "Open"
            ticket.save()
            self.assertTrue(ticket.first_responded_on)
            self.assertIsNone(ticket.on_hold_since)
            self.assertIsNone(ticket.resolution_date)
            self.assertEqual(ticket.agreement_status, "Resolution Due")

    def test_agreement_status_fulfilled(self):
        # Case 7: Resolved within both deadlines → Fulfilled
        # Resolved at T+10min: first_responded_on=T+10min < response_by=T+30min ✓
        # resolution_date=T+10min < resolution_by=T+2h ✓ → Fulfilled
        date = get_current_week_monday(hours=10)
        with self.freeze_time(date):
            ticket = make_ticket(priority="Urgent")

        with self.freeze_time(add_to_date(date, minutes=10)):
            ticket.reload()
            ticket.status = "Resolved"
            ticket.save()
            self.assertEqual(ticket.agreement_status, "Fulfilled")

    def test_failed_by_response(self):
        # Urgent priority: response_by = T+30min
        # Agent replies at T+39min → 9 minutes late in business hours
        date = get_current_week_monday(hours=10)
        with self.freeze_time(date):
            ticket = make_ticket(priority="Urgent")

        with self.freeze_time(add_to_date(date, minutes=39)):
            frappe.set_user(agent)
            ticket.reply_via_agent(message="Test reply after response by")
            ticket.reload()

            ticket.status = "Replied"
            ticket.save()
            ticket.reload()

            self.assertEqual(ticket.agreement_status, "Failed")

            # first_response_failed_by should be 9 minutes (in business hours seconds)
            self.assertEqual(ticket.first_response_failed_by, 9 * 60)

        # now check failed by just 2 minutes after the end time
        # what is the end time of monday?
        # end_time = 6 PM on Monday
        date2 = get_current_week_monday(hours=17)
        with self.freeze_time(add_to_date(date2, minutes=55)):
            ticket2 = make_ticket(priority="Urgent")

        with self.freeze_time(add_to_date(date2, hours=1, minutes=5)):
            frappe.set_user(agent)
            ticket2.reply_via_agent(message="Test reply after response by")
            ticket2.reload()

            ticket2.status = "Replied"
            ticket2.save()
            ticket2.reload()

            self.assertIsNone(ticket2.first_response_failed_by)

    def test_resolution_failed_by(self):
        # Urgent priority: resolution_by = T+2h
        # Ticket resolved at T+2h15min → 15 minutes late in business hours
        date = get_current_week_monday(hours=10)
        with self.freeze_time(date):
            ticket = make_ticket(priority="Urgent")

        with self.freeze_time(add_to_date(date, minutes=135)):
            ticket.reload()
            ticket.status = "Resolved"
            ticket.save()
            ticket.reload()
            self.assertEqual(ticket.agreement_status, "Failed")
            # resolution_failed_by should be 15 minutes (in business hours seconds)
            self.assertEqual(ticket.resolution_failed_by, 15 * 60)

    def test_reply_via_agent_default_sender(self):
        """Without `from_email`, sender on the Communication is the session user."""
        ticket = make_ticket()

        frappe.set_user(agent)
        try:
            ticket.reply_via_agent(message="Reply with default sender")
        finally:
            frappe.set_user("Administrator")

        comm = frappe.get_last_doc(
            "Communication",
            filters={"reference_doctype": "HD Ticket", "reference_name": ticket.name},
        )
        self.assertEqual(comm.sender, agent)

    def test_reply_via_agent_with_from_email(self):
        """When `from_email` is passed, the Communication uses it as sender/email_account."""
        email_account = frappe.get_doc(
            {
                "doctype": "Email Account",
                "email_account_name": "Helpdesk From Email Test",
                "email_id": "from-mail@test.com",
                "domain": "example.com",
                "smtp_server": "smtp.example.com",
                "enable_outgoing": 1,
                "password": "password",
            }
        ).insert(ignore_if_duplicate=True, ignore_permissions=True)

        ticket = make_ticket()
        frappe.set_user(agent)
        try:
            ticket.reply_via_agent(
                message="Reply with switched from email",
                from_email={
                    "email_id": email_account.email_id,
                    "email_account": email_account.name,
                },
            )
        finally:
            frappe.set_user("Administrator")

        comm = frappe.get_last_doc(
            "Communication",
            filters={"reference_doctype": "HD Ticket", "reference_name": ticket.name},
        )
        self.assertEqual(comm.sender, email_account.email_id)
        self.assertEqual(comm.email_account, email_account.name)

    def test_reply_via_agent_with_invalid_from_email_account(self):
        """If `from_email.email_account` does not exist, reply_via_agent should throw."""
        ticket = make_ticket()

        frappe.set_user(agent)
        try:
            with self.assertRaises(frappe.ValidationError):
                ticket.reply_via_agent(
                    message="Reply with bad email account",
                    from_email={
                        "email_id": "invalid@test.com",
                        "email_account": "Invalid Email Account",
                    },
                )
        finally:
            frappe.set_user("Administrator")

    def test_bulk_reply(self):
        """
        bulk_reply on two tickets with two uploaded files should send a reply per
        ticket and attach the files to both the resulting communications and the
        tickets.
        """
        frappe.set_user(agent)

        file1 = upload_test_file("outlook.png")
        file2 = upload_test_file("sendgrid.png")

        ticket1 = make_ticket(raised_by="customer1@test.com")
        ticket2 = make_ticket(raised_by="customer2@test.com")
        ticket_ids = [ticket1.name, ticket2.name]

        bulk_reply(
            ticket_ids=ticket_ids,
            message="Test Message",
            attachments=[file1, file2],
        )

        communications = frappe.get_all(
            "Communication",
            filters={
                "reference_doctype": "HD Ticket",
                "reference_name": ["in", ticket_ids],
                "sent_or_received": "Sent",
            },
            pluck="name",
        )
        self.assertEqual(len(communications), 2)  # one agent reply per ticket

        communication_attachments = frappe.db.count(
            "File",
            {
                "attached_to_doctype": "Communication",
                "attached_to_name": ["in", communications],
            },
        )
        ticket_attachments = frappe.db.count(
            "File",
            {
                "attached_to_doctype": "HD Ticket",
                "attached_to_name": ["in", ticket_ids],
            },
        )

        # Each ticket's communication carries both files, and each ticket carries
        # both files: 2 communications x 2 files and 2 tickets x 2 files.
        self.assertEqual(communication_attachments, 4)
        self.assertEqual(ticket_attachments, 4)

        # delete all files
        files = frappe.get_all(
            "File",
            filters={
                "attached_to_doctype": ["in", ["Communication", "HD Ticket"]],
            },
            pluck="name",
        )
        for file in files:
            frappe.delete_doc("File", file)

    def test_bulk_reply_writes_nothing_if_one_ticket_is_off_limits(self):
        """Everything is checked before anything is written, so a ticket the agent
        cannot reply to stops the batch instead of half completing it."""
        frappe.set_user(agent)
        allowed = make_ticket(raised_by="customer1@test.com")
        forbidden = make_ticket(raised_by="customer2@test.com")

        def deny_forbidden(*args, **kwargs):
            if kwargs.get("doc") == forbidden.name:
                raise frappe.PermissionError
            return True

        with patch("frappe.has_permission", side_effect=deny_forbidden):
            with self.assertRaises(frappe.PermissionError):
                bulk_reply(
                    ticket_ids=[allowed.name, forbidden.name], message="Test Message"
                )

        self.assertFalse(
            sent_replies(allowed.name), "no ticket may be replied to before all pass"
        )

    def test_bulk_reply_replies_once_per_duplicated_ticket(self):
        """Ids are deduped before anything is written, so a ticket listed twice gets
        one reply and one copy of each file."""
        frappe.set_user(agent)
        file1 = upload_test_file("outlook.png")
        ticket = make_ticket(raised_by="customer1@test.com")

        bulk_reply(
            ticket_ids=[ticket.name, ticket.name],
            message="Test Message",
            attachments=[file1],
        )

        self.assertEqual(len(sent_replies(ticket.name)), 1, "one reply, not two")
        self.assertEqual(
            frappe.db.count(
                "File",
                {"attached_to_doctype": "HD Ticket", "attached_to_name": ticket.name},
            ),
            1,
            "one copy of the file, not two",
        )

    def test_auto_close_respects_inactivity_cutoff_boundary(self):
        """`close_tickets_after_n_days` closes a ticket whose last communication is
        older than the inactivity cutoff and keeps one whose last communication
        falls within it. The cutoff is computed in the system timezone, so the
        boundary holds regardless of the database server's timezone."""
        days_threshold = 5
        eligible_status = "Replied"

        settings_fields = [
            "auto_close_tickets",
            "auto_close_status",
            "auto_close_after_days",
        ]
        previous_settings = {
            field: frappe.db.get_single_value("HD Settings", field)
            for field in settings_fields
        }
        frappe.db.set_single_value(
            "HD Settings",
            {
                "auto_close_tickets": 1,
                "auto_close_status": eligible_status,
                "auto_close_after_days": days_threshold,
            },
        )

        cutoff = add_to_date(now_datetime(), days=-days_threshold)
        just_past_cutoff = cutoff - timedelta(minutes=5)  # inactive -> should close
        within_cutoff = cutoff + timedelta(minutes=5)  # still active -> should stay

        stale_ticket = make_ticket()
        fresh_ticket = make_ticket()
        set_ticket_status_and_communication_date(
            stale_ticket.name, eligible_status, just_past_cutoff
        )
        set_ticket_status_and_communication_date(
            fresh_ticket.name, eligible_status, within_cutoff
        )

        try:
            close_tickets_after_n_days()

            self.assertEqual(
                frappe.db.get_value("HD Ticket", stale_ticket.name, "status"),
                "Closed",
                "Ticket inactive past the cutoff should be auto closed",
            )
            self.assertEqual(
                frappe.db.get_value("HD Ticket", fresh_ticket.name, "status"),
                eligible_status,
                "Ticket active within the cutoff should not be closed",
            )
        finally:
            frappe.db.set_single_value("HD Settings", previous_settings)

    def make_test_sla(self, name, condition, rank=0, priorities=None):
        """Create a conditional SLA and disable it once the test ends."""
        sla = make_sla(name, condition, rank=rank, priorities=priorities)
        self.addCleanup(frappe.db.set_value, SLA_DOCTYPE, sla.name, "enabled", 0)
        return sla

    def demote_default_sla(self):
        """Leave the site with no Default SLA, restored once the test ends."""
        self.addCleanup(set_default_sla, DEFAULT_SLA, 1)
        set_default_sla(DEFAULT_SLA, 0)

    def test_ticket_without_sla(self):
        """A priority that no SLA includes leaves every SLA field blank."""
        make_priority(UNINCLUDED_PRIORITY)

        ticket = make_ticket(priority=UNINCLUDED_PRIORITY)

        self.assertFalse(ticket.sla)
        self.assertFalse(ticket.agreement_status)
        self.assertFalse(ticket.response_by)
        self.assertFalse(ticket.resolution_by)
        self.assertFalse(ticket.service_level_agreement_creation)

    def test_ticket_without_default_sla(self):
        """With no Default SLA on the site, an unmatched ticket gets no SLA."""
        self.demote_default_sla()

        # Medium is included everywhere but matched by no condition
        ticket = make_ticket(priority="Medium")

        self.assertFalse(ticket.sla)
        self.assertFalse(ticket.response_by)

    def test_sla_skipped_when_it_does_not_include_priority(self):
        """A matching policy that lacks the priority is passed over, not the end of the walk."""
        condition = "doc.priority == 'High'"
        self.make_test_sla("Skipped SLA", condition, rank=10, priorities=["Low"])
        applied = self.make_test_sla(
            "Applied SLA", condition, rank=20, priorities=["High"]
        )

        ticket = make_ticket(priority="High")

        self.assertEqual(ticket.sla, applied.name)

    def test_sla_applied_when_condition_matches_later(self):
        """A blank ticket picks up a policy on the save that makes it match."""
        make_priority(UNINCLUDED_PRIORITY)
        ticket = make_ticket(priority=UNINCLUDED_PRIORITY)
        self.assertFalse(ticket.sla)
        self.assertFalse(ticket.service_level_agreement_creation)

        sla = self.make_test_sla(
            "Late Match SLA",
            f"doc.priority == '{UNINCLUDED_PRIORITY}'",
            priorities=[UNINCLUDED_PRIORITY],
        )
        ticket.reload()
        ticket.save()

        self.assertEqual(ticket.sla, sla.name)
        self.assertTrue(ticket.response_by)
        self.assertTrue(ticket.service_level_agreement_creation)
        self.assertEqual(ticket.agreement_status, "First Response Due")

    def test_sla_clock_starts_at_attach_not_creation(self):
        """A late attach counts from the attach, not from when the ticket was raised."""
        make_priority(UNINCLUDED_PRIORITY)
        raised_at = get_current_week_monday(hours=12)
        with self.freeze_time(raised_at):
            ticket = make_ticket(priority=UNINCLUDED_PRIORITY)

        sla = self.make_test_sla(
            "Attach Clock SLA",
            f"doc.priority == '{UNINCLUDED_PRIORITY}'",
            priorities=[UNINCLUDED_PRIORITY],
        )
        attached_at = add_to_date(raised_at, hours=2)
        with self.freeze_time(attached_at):
            ticket.reload()
            ticket.save()

        self.assertEqual(ticket.sla, sla.name)
        self.assertEqual(
            get_datetime(ticket.service_level_agreement_creation), attached_at
        )
        response_time, _ = get_priority_response_resolution_time(
            sla.name, UNINCLUDED_PRIORITY, add_to_time=False
        )
        self.assertEqual(
            ticket.response_by, add_to_date(attached_at, seconds=response_time)
        )

    def test_sla_targets_stable_across_repeated_saves(self):
        """Once attached, targets are anchored and must not slide on later saves."""
        make_priority(UNINCLUDED_PRIORITY)
        raised_at = get_current_week_monday(hours=12)
        with self.freeze_time(raised_at):
            ticket = make_ticket(priority=UNINCLUDED_PRIORITY)

        self.make_test_sla(
            "Stable Clock SLA",
            f"doc.priority == '{UNINCLUDED_PRIORITY}'",
            priorities=[UNINCLUDED_PRIORITY],
        )
        with self.freeze_time(add_to_date(raised_at, hours=1)):
            ticket.reload()
            ticket.save()
        response_by, resolution_by = ticket.response_by, ticket.resolution_by

        with self.freeze_time(add_to_date(raised_at, hours=2)):
            ticket.reload()
            ticket.subject = "Saved again"
            ticket.save()

        self.assertEqual(ticket.response_by, response_by)
        self.assertEqual(ticket.resolution_by, resolution_by)

    def test_sla_removed_when_condition_stops_matching(self):
        """A ticket that stops matching every policy loses its SLA and its targets."""
        make_priority(UNINCLUDED_PRIORITY)
        ticket = make_ticket(priority="High")
        self.assertEqual(ticket.sla, SLA_PRIORITY_NAME)
        anchor = ticket.service_level_agreement_creation

        ticket.reload()
        ticket.priority = UNINCLUDED_PRIORITY  # matched by nothing
        ticket.save()

        self.assertFalse(ticket.sla)
        self.assertFalse(ticket.response_by)
        self.assertFalse(ticket.resolution_by)
        self.assertFalse(ticket.agreement_status)
        # the clock keeps running, so flapping the condition buys no time
        self.assertEqual(ticket.service_level_agreement_creation, anchor)

    def test_no_detach_while_default_sla_enabled(self):
        """With a Default SLA on the site a ticket falls back to it rather than detaching."""
        ticket = make_ticket(priority="High")
        self.assertEqual(ticket.sla, SLA_PRIORITY_NAME)

        ticket.reload()
        ticket.priority = (
            "Medium"  # no condition matches, but the Default SLA includes it
        )
        ticket.save()

        self.assertEqual(ticket.sla, DEFAULT_SLA)
        self.assertTrue(ticket.response_by)

    def test_detach_keeps_breach_facts(self):
        """Detaching drops the promises a policy made, not the record of missing them."""
        # Urgent: response_by = T+30min, and the agent replies 9 minutes late
        make_priority(UNINCLUDED_PRIORITY)
        raised_at = get_current_week_monday(hours=10)
        with self.freeze_time(raised_at):
            ticket = make_ticket(priority="Urgent")

        with self.freeze_time(add_to_date(raised_at, minutes=39)):
            frappe.set_user(agent)
            ticket.reply_via_agent(message="Late reply")
            ticket.reload()
            ticket.status = "Replied"
            ticket.save()
        self.assertEqual(ticket.agreement_status, "Failed")

        ticket.reload()
        ticket.priority = UNINCLUDED_PRIORITY
        ticket.save()

        self.assertFalse(ticket.sla)
        self.assertFalse(ticket.response_by)
        self.assertEqual(ticket.agreement_status, "Failed")
        self.assertEqual(ticket.first_response_failed_by, 9 * 60)
        self.assertTrue(ticket.first_response_time)

    def test_anchor_survives_detach_and_reattach(self):
        """A policy picked up again recomputes from the original clock start."""
        make_priority(UNINCLUDED_PRIORITY)
        raised_at = get_current_week_monday(hours=12)
        with self.freeze_time(raised_at):
            ticket = make_ticket(priority="High")
        self.assertEqual(ticket.sla, SLA_PRIORITY_NAME)

        with self.freeze_time(add_to_date(raised_at, hours=1)):
            ticket.reload()
            ticket.priority = UNINCLUDED_PRIORITY
            ticket.save()
        self.assertFalse(ticket.sla)

        with self.freeze_time(add_to_date(raised_at, hours=2)):
            ticket.reload()
            ticket.priority = "High"
            ticket.save()

        self.assertEqual(ticket.sla, SLA_PRIORITY_NAME)
        self.assertEqual(
            get_datetime(ticket.service_level_agreement_creation), raised_at
        )
        response_time, _ = get_priority_response_resolution_time(
            SLA_PRIORITY_NAME, "High", add_to_time=False
        )
        self.assertEqual(
            ticket.response_by, add_to_date(raised_at, seconds=response_time)
        )

    def test_sla_swap_keeps_original_clock_start(self):
        """Swapping policies recomputes targets from the original clock start."""
        raised_at = get_current_week_monday(hours=12)
        with self.freeze_time(raised_at):
            ticket = make_ticket(priority="High")
        self.assertEqual(ticket.sla, SLA_PRIORITY_NAME)

        # Medium is matched by no other condition, so the swap target is unambiguous
        swapped_to = self.make_test_sla(
            "Swap Target SLA", "doc.priority == 'Medium'", priorities=["Medium"]
        )
        with self.freeze_time(add_to_date(raised_at, hours=1)):
            ticket.reload()
            ticket.priority = "Medium"
            ticket.save()

        self.assertEqual(ticket.sla, swapped_to.name)
        self.assertEqual(
            get_datetime(ticket.service_level_agreement_creation), raised_at
        )
        response_time, _ = get_priority_response_resolution_time(
            swapped_to.name, "Medium", add_to_time=False
        )
        self.assertEqual(
            ticket.response_by, add_to_date(raised_at, seconds=response_time)
        )

    def test_lower_rank_sla_wins(self):
        """Between two matching policies, the lower rank is applied."""
        condition = "doc.priority == 'Medium'"
        # created first, so winning on creation order would hide the rank
        self.make_test_sla("Rank Five SLA", condition, rank=5, priorities=["Medium"])
        winner = self.make_test_sla(
            "Rank One SLA", condition, rank=1, priorities=["Medium"]
        )

        ticket = make_ticket(priority="Medium")

        self.assertEqual(ticket.sla, winner.name)

    def test_unranked_sla_applied_after_ranked(self):
        """Rank 0 means unranked, so it loses even to a high rank number."""
        condition = "doc.priority == 'Medium'"
        self.make_test_sla("Unranked SLA", condition, rank=0, priorities=["Medium"])
        ranked = self.make_test_sla(
            "Ranked Last SLA", condition, rank=5, priorities=["Medium"]
        )

        ticket = make_ticket(priority="Medium")

        self.assertEqual(ticket.sla, ranked.name)

    def test_default_sla_applied_only_when_no_condition_matches(self):
        """The Default SLA is considered last, even when it carries the best rank."""
        frappe.db.set_value(SLA_DOCTYPE, DEFAULT_SLA, "rank", 1)
        self.addCleanup(frappe.db.set_value, SLA_DOCTYPE, DEFAULT_SLA, "rank", 0)
        matched = self.make_test_sla(
            "Worst Rank SLA", "doc.priority == 'Medium'", rank=99, priorities=["Medium"]
        )

        self.assertEqual(make_ticket(priority="Medium").sla, matched.name)

        frappe.db.set_value(SLA_DOCTYPE, matched.name, "enabled", 0)
        unmatched = make_ticket(subject="Nothing matches", priority="Medium")
        self.assertEqual(unmatched.sla, DEFAULT_SLA)

    def test_ticket_without_sla_uses_settings_default_status(self):
        """A blank ticket takes its status from HD Settings, not an arbitrary policy."""
        make_priority(UNINCLUDED_PRIORITY)
        sla_only_status = make_status(name="SLA Only Status")
        status_field = "default_ticket_status"
        frappe.db.set_value(
            SLA_DOCTYPE, SLA_PRIORITY_NAME, status_field, sla_only_status.name
        )
        self.addCleanup(
            frappe.db.set_value, SLA_DOCTYPE, SLA_PRIORITY_NAME, status_field, None
        )

        ticket = make_ticket(priority=UNINCLUDED_PRIORITY)

        self.assertFalse(ticket.sla)
        self.assertEqual(
            ticket.status,
            frappe.db.get_single_value("HD Settings", "default_ticket_status"),
        )

    def test_resolution_date_set_without_sla(self):
        """Resolving a blank ticket stamps resolution_date; the durations stay blank."""
        make_priority(UNINCLUDED_PRIORITY)
        ticket = make_ticket(priority=UNINCLUDED_PRIORITY)
        self.assertFalse(ticket.sla)

        ticket.reload()
        ticket.status = "Resolved"
        ticket.save()

        self.assertTrue(ticket.resolution_date)
        self.assertFalse(ticket.resolution_time)

    def test_reopening_a_detached_ticket_clears_resolution_time(self):
        """Reopening must not leave a resolution duration behind with no resolution date."""
        make_priority(UNINCLUDED_PRIORITY)
        raised_at = get_current_week_monday(hours=12)
        with self.freeze_time(raised_at):
            ticket = make_ticket(priority="High")

        with self.freeze_time(add_to_date(raised_at, hours=1)):
            ticket.reload()
            ticket.status = "Resolved"
            ticket.save()
        self.assertTrue(ticket.resolution_time)

        ticket.reload()
        ticket.priority = UNINCLUDED_PRIORITY  # detaches, so no SLA runs on the reopen
        ticket.status = "Open"
        ticket.save()

        self.assertFalse(ticket.sla)
        self.assertFalse(ticket.resolution_date)
        self.assertFalse(ticket.resolution_time)

    def test_detached_time_is_not_billed_as_hold_time(self):
        """Detaching while paused must not credit the detached window as hold."""
        make_priority(UNINCLUDED_PRIORITY)
        raised_at = get_current_week_monday(hours=10)
        with self.freeze_time(raised_at):
            ticket = make_ticket(priority="High")

        with self.freeze_time(add_to_date(raised_at, minutes=10)):
            ticket.reload()
            ticket.status = "Replied"  # pauses the clock
            ticket.save()
        self.assertTrue(ticket.on_hold_since)

        # un-pause and detach on the same save, so set_hold_time never runs
        with self.freeze_time(add_to_date(raised_at, minutes=20)):
            ticket.reload()
            ticket.priority = UNINCLUDED_PRIORITY
            ticket.status = "Open"
            ticket.save()
        self.assertFalse(ticket.sla)
        self.assertFalse(ticket.on_hold_since)

        # an hour later it matches again; the detached hour must not count as hold
        with self.freeze_time(add_to_date(raised_at, minutes=80)):
            ticket.reload()
            ticket.priority = "High"
            ticket.status = "Replied"
            ticket.save()

        self.assertEqual(ticket.sla, SLA_PRIORITY_NAME)
        self.assertFalse(ticket.total_hold_time)

    def test_detaching_while_paused_keeps_the_pause_anchor(self):
        """A ticket that stays paused across a detach must keep its hold credit."""
        make_priority(UNINCLUDED_PRIORITY)
        raised_at = get_current_week_monday(hours=10)
        with self.freeze_time(raised_at):
            ticket = make_ticket(priority="High")
        resolution_by = ticket.resolution_by

        with self.freeze_time(add_to_date(raised_at, minutes=10)):
            ticket.reload()
            ticket.status = "Replied"  # pauses the clock
            ticket.save()

        # detach without touching status, so the ticket is still paused
        with self.freeze_time(add_to_date(raised_at, minutes=20)):
            ticket.reload()
            ticket.priority = UNINCLUDED_PRIORITY
            ticket.save()
        self.assertFalse(ticket.sla)
        self.assertTrue(ticket.on_hold_since)

        with self.freeze_time(add_to_date(raised_at, minutes=30)):
            ticket.reload()
            ticket.priority = "High"
            ticket.save()
        self.assertEqual(ticket.agreement_status, "Paused")

        # un-pausing bills the whole pause, so the deadline moves out by it
        with self.freeze_time(add_to_date(raised_at, minutes=40)):
            ticket.reload()
            ticket.status = "Open"
            ticket.save()

        self.assertEqual(ticket.total_hold_time, 30 * 60)
        self.assertEqual(
            get_datetime(ticket.resolution_by),
            add_to_date(get_datetime(resolution_by), minutes=30),
        )

    def test_unpausing_while_detached_drops_the_pause_anchor(self):
        """A detached ticket has no SLA to finalise its hold, so leaving Paused
        must drop the anchor rather than bank the gap as hold time."""
        make_priority(UNINCLUDED_PRIORITY)
        raised_at = get_current_week_monday(hours=10)
        with self.freeze_time(raised_at):
            ticket = make_ticket(priority="High")

        with self.freeze_time(add_to_date(raised_at, minutes=10)):
            ticket.reload()
            ticket.status = "Replied"  # pauses the clock
            ticket.save()

        # detach while still paused, so the anchor is deliberately kept
        with self.freeze_time(add_to_date(raised_at, minutes=20)):
            ticket.reload()
            ticket.priority = UNINCLUDED_PRIORITY
            ticket.save()
        self.assertTrue(ticket.on_hold_since)

        # un-pause with no SLA attached: nothing can finalise the hold
        with self.freeze_time(add_to_date(raised_at, minutes=30)):
            ticket.reload()
            ticket.status = "Open"
            ticket.save()
        self.assertFalse(ticket.sla)
        self.assertFalse(ticket.on_hold_since)

        # re-attaching must not treat the open, detached window as hold
        with self.freeze_time(add_to_date(raised_at, minutes=90)):
            ticket.reload()
            ticket.priority = "High"
            ticket.status = "Replied"
            ticket.save()

        self.assertEqual(ticket.sla, SLA_PRIORITY_NAME)
        self.assertFalse(ticket.total_hold_time)

    def test_permission_check_answers_for_passed_user_not_session(self):
        """A check made on behalf of another user must use that user's teams.

        Session is an agent on the ticket's team, the checked user is not, so a
        session-bound lookup would wrongly grant access.
        """
        make_team("Team A", members=[agent])
        make_team("Team B", members=[agent2])
        frappe.db.set_single_value("HD Settings", "restrict_tickets_by_agent_group", 1)
        self.addCleanup(
            frappe.db.set_single_value,
            "HD Settings",
            "restrict_tickets_by_agent_group",
            0,
        )

        ticket = make_ticket(agent_group="Team B", raised_by=non_agent)

        frappe.set_user(agent2)
        self.assertTrue(has_permission(ticket, user=agent2))
        self.assertFalse(has_permission(ticket, user=agent))
        self.assertNotIn("Team B", permission_query(agent))

    def tearDown(self):
        frappe.set_user("Administrator")
        remove_holidays()
        frappe.db.set_single_value("HD Settings", "default_ticket_status", "Open")
        frappe.delete_doc("HD Ticket Status", "New", force=True)
