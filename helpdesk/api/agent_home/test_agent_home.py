# Copyright (c) 2024, Frappe Technologies and Contributors
# See license.txt

import json

import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.api.agent_home.agent_home import (
    get_agent_tickets,
    get_avg_first_response_time,
    get_avg_resolution_time,
    get_avg_time_metrics,
    get_dashboard,
    get_default_agent_dashboard,
    get_pending_tickets,
    get_recent_feedback,
)
from helpdesk.test_utils import make_agent, make_sla, make_ticket

agent_email = "test_agent@test.com"


def set_ticket_timestamps(
    ticket_name: str,
    creation=None,
    modified=None,
    first_response_time=None,
    resolution_time=None,
):
    """
    Updates ticket timestamps directly in the database.
    Useful for creating test tickets with specific dates.
    """
    if creation:
        frappe.db.set_value("HD Ticket", ticket_name, "creation", creation)

    if modified:
        frappe.db.sql(
            "UPDATE `tabHD Ticket` SET modified=%s WHERE name=%s",
            (modified, ticket_name),
        )

    if first_response_time:
        frappe.db.set_value(
            "HD Ticket", ticket_name, "first_response_time", first_response_time
        )

    if resolution_time:
        frappe.db.set_value(
            "HD Ticket", ticket_name, "resolution_time", resolution_time
        )


def create_ticket_with_agent(
    agent: str = None,
    creation=None,
    modified=None,
    first_response_time=None,
    resolution_time=None,
    **kwargs,
):
    """
    Creates a ticket with flexible options including agent assignment and timestamps.
    Combines make_ticket functionality with agent assignment and timestamp setting.
    """
    ticket = make_ticket(**kwargs)

    if agent:
        ticket.assign_agent(agent)

    if creation or modified or first_response_time or resolution_time:
        set_ticket_timestamps(
            ticket.name,
            creation=creation,
            modified=modified,
            first_response_time=first_response_time,
            resolution_time=resolution_time,
        )

    return ticket


class TestAgentHome(IntegrationTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        make_agent(agent_email, "Test Agent")
        frappe.set_user(agent_email)

    @classmethod
    def tearDownClass(cls):
        frappe.set_user("Administrator")
        super().tearDownClass()

    def setUp(self):
        frappe.set_user(agent_email)
        # Clean up tickets before each test
        frappe.db.delete("HD Ticket")
        frappe.db.delete("HD Field Layout", {"user": agent_email})
        frappe.db.commit()  # nosemgrep

    def _create_ticket(
        self,
        agent=None,
        creation=None,
        modified=None,
        first_response_time=None,
        resolution_time=None,
        **kwargs,
    ):
        """Helper to create a ticket with flexible options"""
        if agent is None:
            agent = agent_email

        # Use default values if not provided in kwargs
        if "subject" not in kwargs:
            kwargs["subject"] = "Test Ticket"
        if "description" not in kwargs:
            kwargs["description"] = "Test Description"

        return create_ticket_with_agent(
            agent=agent,
            creation=creation,
            modified=modified,
            first_response_time=first_response_time,
            resolution_time=resolution_time,
            **kwargs,
        )

    def test_returns_valid_json(self):
        """Test that default dashboard returns valid JSON string"""
        result = get_default_agent_dashboard()
        self.assertIsInstance(result, str)

        # Should be parseable as JSON
        parsed = json.loads(result)
        self.assertIsInstance(parsed, list)

    def test_get_dashboard_with_existing_layout(self):
        """Test dashboard retrieval when layout exists"""
        # Create a layout for the user
        layout_doc = frappe.get_doc(
            {
                "doctype": "HD Field Layout",
                "user": agent_email,
                "layout": get_default_agent_dashboard(),
            }
        ).insert(ignore_permissions=True)

        result = get_dashboard()

        self.assertEqual(result["dashboard_id"], layout_doc.name)

    def test_reset_layout(self):
        """Test dashboard reset functionality"""
        # Create a custom layout
        custom_layout = json.dumps([{"chart": "custom_chart", "layout": {}}])
        frappe.get_doc(
            {
                "doctype": "HD Field Layout",
                "user": agent_email,
                "layout": custom_layout,
            }
        ).insert(ignore_permissions=True)

        result = get_dashboard(reset_layout=True)

        # Should return default layout structure
        default_layout = json.loads(get_default_agent_dashboard())
        self.assertEqual(len(result["layout"]), len(default_layout))

    def test_get_agent_tickets_different_periods(self):
        """Test different period options"""
        now = frappe.utils.nowdate()

        # T1: 2 days ago (matches all periods: week, month, 3 months)
        self._create_ticket(
            creation=frappe.utils.add_days(now, -2),
            subject="Ticket 2 days ago",
        )

        # T2: 10 days ago (matches: month, 3 months)
        self._create_ticket(
            creation=frappe.utils.add_days(now, -10),
            subject="Ticket 10 days ago",
        )

        # T3: 40 days ago (matches: 3 months only)
        self._create_ticket(
            creation=frappe.utils.add_days(now, -40),
            subject="Ticket 40 days ago",
        )

        # Test last week (7 days) - Should see 1 ticket (T1)
        result = get_agent_tickets(period="last week")
        self.assertIn("data", result)
        self.assertIn("total", result)
        self.assertIn("percentage_change", result)
        self.assertEqual(result["total"], 1)
        # Verify data is a list with date entries
        self.assertIsInstance(result["data"], list)
        self.assertEqual(len(result["data"]), 7)  # 7 days of data

        # Test last month (30 days) - Should see 2 tickets (T1, T2)
        result = get_agent_tickets(period="last month")
        self.assertEqual(result["total"], 2)
        self.assertEqual(len(result["data"]), 30)  # 30 days of data

        # Test last 3 months (90 days) - Should see 3 tickets (T1, T2, T3)
        result = get_agent_tickets(period="last 3 months")
        self.assertEqual(result["total"], 3)
        self.assertEqual(len(result["data"]), 90)  # 90 days of data

    def test_get_agent_tickets_count_per_agent(self):
        """Test that ticket count is retrieved correctly for each agent"""
        # Create a second agent
        second_agent_email = "test_agent_2@test.com"
        make_agent(second_agent_email, "Test Agent 2")

        # Create 2 tickets assigned to the first agent (test_agent@test.com)
        self._create_ticket()
        self._create_ticket()

        # Create 3 tickets assigned to the second agent
        for _ in range(3):
            self._create_ticket(
                agent=second_agent_email,
                subject="Test Ticket for Agent 2",
            )

        # Verify first agent sees only their 2 tickets
        frappe.set_user(agent_email)
        result = get_agent_tickets()
        self.assertEqual(result["total"], 2)

        # Verify second agent sees only their 3 tickets
        frappe.set_user(second_agent_email)
        result = get_agent_tickets()
        self.assertEqual(result["total"], 3)

        # Switch back to original agent
        frappe.set_user(agent_email)

    def _test_avg_metric(self, method, field_name):
        """Helper to test average time metric calculations"""

        # Create tickets for "Current" period (Last 30 days)
        # Using 2 days ago
        current_date_1 = frappe.utils.add_days(frappe.utils.nowdate(), -2)
        self._create_ticket(
            creation=current_date_1, **{field_name: 30}
        )  # 30 mins/hours
        self._create_ticket(
            creation=current_date_1, **{field_name: 60}
        )  # 60 mins/hours
        # Current Avg = (30 + 60) / 2 = 45

        # Create tickets for "Previous" period (30-60 days ago)
        # Using 35 days ago
        previous_date_1 = frappe.utils.add_days(frappe.utils.nowdate(), -35)
        self._create_ticket(
            creation=previous_date_1, **{field_name: 20}
        )  # 20 mins/hours
        self._create_ticket(
            creation=previous_date_1, **{field_name: 40}
        )  # 40 mins/hours
        # Previous Avg = (20 + 40) / 2 = 30

        # Calculate Expected Percentage Change
        # ((Current - Previous) / Previous) * 100
        # ((45 - 30) / 30) * 100 = (15 / 30) * 100 = 50.0

        result = method(period="last month")

        self.assertEqual(result["average"], 45.0)
        self.assertEqual(result["percentage_change"], 50.0)

    def test_get_avg_first_response_time(self):
        """Test average first response time calculation"""
        self._test_avg_metric(get_avg_first_response_time, "first_response_time")

    def test_get_avg_resolution_time(self):
        """Test average resolution time calculation"""
        self._test_avg_metric(get_avg_resolution_time, "resolution_time")

    def test_get_recent_feedback_rating_distribution(self):
        """Test average and distribution calculations with multiple feedbacks"""
        # Create multiple tickets with different ratings
        self._create_ticket(feedback_rating=1.0)  # 5 stars
        self._create_ticket(feedback_rating=0.6)  # 3 stars
        self._create_ticket(feedback_rating=0.2)  # 1 star

        # Avg = (5 + 3 + 1) / 3 = 3.0

        result = get_recent_feedback()

        self.assertEqual(result["total_feedbacks"], 3)
        self.assertEqual(result["average_rating"], 3.0)

        dist = result["rating_distribution"]
        self.assertEqual(dist[5], 1)
        self.assertEqual(dist[3], 1)
        self.assertEqual(dist[1], 1)
        self.assertEqual(dist[2], 0)
        self.assertEqual(dist[4], 0)

    def test_get_recent_feedback_different_periods(self):
        """Test different period options"""
        # Create tickets with different ages
        now = frappe.utils.now_datetime()

        # T1: Today (matches all periods)
        self._create_ticket(feedback_rating=1.0, modified=now)

        # T2: 10 days ago (matches last month, last 3 months, all time)
        self._create_ticket(
            feedback_rating=0.8, modified=frappe.utils.add_days(now, -10)
        )

        # T3: 40 days ago (matches last 3 months, all time)
        self._create_ticket(
            feedback_rating=0.6, modified=frappe.utils.add_days(now, -40)
        )

        # T4: 100 days ago (only matches all time)
        self._create_ticket(
            feedback_rating=0.4, modified=frappe.utils.add_days(now, -100)
        )

        # Test last_week (7 days) - Should see 1 ticket
        result = get_recent_feedback(period="last_week")
        self.assertEqual(result["total_feedbacks"], 1)
        self.assertEqual(result["average_rating"], 5.0)

        # Test last_month (30 days) - Should see 2 tickets (T1, T2)
        result = get_recent_feedback(period="last_month")
        self.assertEqual(result["total_feedbacks"], 2)
        # Avg = (5 + 4) / 2 = 4.5
        self.assertEqual(result["average_rating"], 4.5)

        # Test last_3_months (90 days) - Should see 3 tickets (T1, T2, T3)
        result = get_recent_feedback(period="last_3_months")
        self.assertEqual(result["total_feedbacks"], 3)
        # Avg = (5 + 4 + 3) / 3 = 4.0
        self.assertEqual(result["average_rating"], 4.0)

        # Test all_time - Should see 4 tickets
        result = get_recent_feedback(period="all_time")
        self.assertEqual(result["total_feedbacks"], 4)
        # Avg = (5 + 4 + 3 + 2) / 4 = 3.5
        self.assertEqual(result["average_rating"], 3.5)

    def test_get_recent_feedback_sort_order(self):
        """Test sort order options"""
        # Create tickets with different ratings
        self._create_ticket(feedback_rating=1.0)  # 5 stars
        self._create_ticket(feedback_rating=0.6)  # 3 stars
        self._create_ticket(feedback_rating=0.2)  # 1 star

        # Test positive_first (Descending)
        result = get_recent_feedback(sort_order="positive_first")
        feedbacks = result["recent_feedbacks"]
        self.assertEqual(len(feedbacks), 3)
        self.assertEqual(feedbacks[0]["feedback_rating"], 1.0)
        self.assertEqual(feedbacks[1]["feedback_rating"], 0.6)
        self.assertEqual(feedbacks[2]["feedback_rating"], 0.2)

        # Test negative_first (Ascending)
        result = get_recent_feedback(sort_order="negative_first")
        feedbacks = result["recent_feedbacks"]
        self.assertEqual(len(feedbacks), 3)
        self.assertEqual(feedbacks[0]["feedback_rating"], 0.2)
        self.assertEqual(feedbacks[1]["feedback_rating"], 0.6)
        self.assertEqual(feedbacks[2]["feedback_rating"], 1.0)

    def test_get_avg_time_metrics_different_periods(self):
        """Test different period options with actual data verification"""
        now = frappe.utils.now_datetime()

        # Create tickets spread across the last year
        # T1: 1 month ago (matches 3m, 6m, 1y)
        self._create_ticket(
            creation=frappe.utils.add_months(now, -1),
            first_response_time=10,
            resolution_time=20,
        )

        # T2: 4 months ago (matches 6m, 1y)
        self._create_ticket(
            creation=frappe.utils.add_months(now, -4),
            first_response_time=20,
            resolution_time=40,
        )

        # T3: 8 months ago (matches 1y)
        self._create_ticket(
            creation=frappe.utils.add_months(now, -8),
            first_response_time=30,
            resolution_time=60,
        )

        # Test 3m period (Should see T1 only)
        # Avg First = 10, Avg Res = 20
        result = get_avg_time_metrics(period="3m")
        self.assertEqual(result["averages"]["first_response"], 10.0)
        self.assertEqual(result["averages"]["resolution"], 20.0)

        # Verify data points exist for the months
        month_labels = [row[0] for row in result["data"]]
        t1_month = frappe.utils.add_months(now, -1).strftime("%b")
        self.assertIn(t1_month, month_labels)

        # Test 6m period (Should see T1, T2)
        # Avg First = (10 + 20) / 2 = 15
        # Avg Res = (20 + 40) / 2 = 30
        result = get_avg_time_metrics(period="6m")
        self.assertEqual(result["averages"]["first_response"], 15.0)
        self.assertEqual(result["averages"]["resolution"], 30.0)

        # Test 1y period (Should see T1, T2, T3)
        # Avg First = (10 + 20 + 30) / 3 = 20
        # Avg Res = (20 + 40 + 60) / 3 = 40
        result = get_avg_time_metrics(period="1y")
        self.assertEqual(result["averages"]["first_response"], 20.0)
        self.assertEqual(result["averages"]["resolution"], 40.0)

    def _create_ticket_with_sla(self, priority="High", agent=None):
        """Helper to create a ticket with SLA"""
        # Create SLA with condition for the priority
        condition = f"doc.priority == '{priority}'"
        sla = make_sla(f"Test SLA {priority}", condition)

        # Configure SLA with priority settings
        sla.reload()

        # Clear and set support days to avoid duplicate workday validation errors
        sla.support_and_resolution = []
        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
            sla.append(
                "support_and_resolution",
                {
                    "workday": day,
                    "start_time": "10:00:00",
                    "end_time": "18:00:00",
                },
            )

        sla.priorities = []
        sla.append(
            "priorities",
            {
                "priority": priority,
                "default_priority": 1,
                "response_time": 60 * 60,  # 1 hour
                "resolution_time": 60 * 60 * 4,  # 4 hours
            },
        )
        sla.save()

        # Create ticket with the specified priority
        ticket = self._create_ticket(
            subject="SLA Test Ticket", priority=priority, agent=agent
        )

        # Ensure SLA fields are set for upcoming_sla tests
        ticket.reload()
        return ticket

    def test_get_pending_tickets_upcoming_sla_type(self):
        """Test getting upcoming SLA violation tickets"""
        # Create a second agent for non-matching tickets
        other_agent_email = "other_agent_sla@test.com"
        make_agent(other_agent_email, "Other Agent SLA")

        # Create SLA ticket for current agent
        ticket = self._create_ticket_with_sla(priority="High")

        # Create SLA ticket for OTHER agent (should NOT be returned)
        other_ticket = self._create_ticket_with_sla(
            priority="High", agent=other_agent_email
        )

        result = get_pending_tickets(ticket_type="upcoming_sla")

        # Verify our SLA ticket is in the result
        ticket_names = [t["name"] for t in result["tickets"]]
        self.assertIn(ticket.name, ticket_names)
        # Other agent's ticket should NOT be in the result
        self.assertNotIn(other_ticket.name, ticket_names)

    def test_get_pending_tickets_new_tickets_type(self):
        """Test getting newly assigned tickets"""
        # Create a second agent for non-matching tickets
        other_agent_email = "other_agent_new@test.com"
        make_agent(other_agent_email, "Other Agent New")

        # Create new tickets for current agent
        ticket1 = self._create_ticket(subject="New Test Ticket 1")
        ticket2 = self._create_ticket(subject="New Test Ticket 2")
        ticket3 = self._create_ticket(subject="New Test Ticket 3")

        # Create tickets assigned to OTHER agent (should NOT be returned)
        self._create_ticket(agent=other_agent_email, subject="Other Agent New Ticket 1")
        self._create_ticket(agent=other_agent_email, subject="Other Agent New Ticket 2")

        result = get_pending_tickets(ticket_type="new_tickets")

        self.assertIn("tickets", result)
        self.assertIn("total_pending_tickets", result)
        # Only current agent's new tickets should be returned
        self.assertEqual(result["total_pending_tickets"], 3)

        # Verify all new tickets are in the result
        ticket_names = [t["name"] for t in result["tickets"]]
        self.assertIn(ticket1.name, ticket_names)
        self.assertIn(ticket2.name, ticket_names)
        self.assertIn(ticket3.name, ticket_names)

        # Verify reason format
        for t in result["tickets"]:
            self.assertEqual(t["reason"]["type"], "new_tickets")
            self.assertEqual(t["reason"]["text"], "Recently assigned")

    def test_get_pending_tickets_pending_type(self):
        """Test getting tickets pending response"""
        # Create a second agent for non-matching tickets
        other_agent_email = "other_agent_pending@test.com"
        make_agent(other_agent_email, "Other Agent Pending")

        # Create tickets pending response for current agent
        ticket1 = self._create_ticket(subject="Pending Response Ticket 1")
        frappe.get_doc(
            {
                "doctype": "Communication",
                "communication_type": "Communication",
                "reference_doctype": "HD Ticket",
                "reference_name": ticket1.name,
                "sent_or_received": "Received",
                "content": "Customer message 1",
            }
        ).insert(ignore_permissions=True)

        ticket2 = self._create_ticket(subject="Pending Response Ticket 2")
        frappe.get_doc(
            {
                "doctype": "Communication",
                "communication_type": "Communication",
                "reference_doctype": "HD Ticket",
                "reference_name": ticket2.name,
                "sent_or_received": "Received",
                "content": "Customer message 2",
            }
        ).insert(ignore_permissions=True)

        # Create ticket for OTHER agent with communication (should NOT be returned)
        other_ticket = self._create_ticket(
            agent=other_agent_email, subject="Other Agent Pending Ticket"
        )
        frappe.get_doc(
            {
                "doctype": "Communication",
                "communication_type": "Communication",
                "reference_doctype": "HD Ticket",
                "reference_name": other_ticket.name,
                "sent_or_received": "Received",
                "content": "Other agent customer message",
            }
        ).insert(ignore_permissions=True)

        result = get_pending_tickets(ticket_type="pending")

        # Verify current agent's pending tickets are returned
        self.assertGreaterEqual(result["total_pending_tickets"], 2)

        # Verify pending tickets are in the result
        ticket_names = [t["name"] for t in result["tickets"]]
        self.assertIn(ticket1.name, ticket_names)
        self.assertIn(ticket2.name, ticket_names)

        # Verify reason format
        for t in result["tickets"]:
            self.assertEqual(t["reason"]["type"], "pending")
            self.assertIn("Pending for", t["reason"]["text"])
