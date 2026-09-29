import json

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, getdate, now_datetime, nowdate

from helpdesk.api.dashboard import HelpdeskDashboard, get_dashboard_data
from helpdesk.test_utils import (
    create_agent,
    create_contact,
    make_agent_manager,
    make_sla,
    make_tagged_ticket,
    make_team,
    make_ticket,
    unique_email,
)

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


class TestTagDashboard(IntegrationTestCase):
    """Tag charts reached through `get_dashboard_data("tags", ...)`."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.manager = make_agent_manager("tag-dash-manager")
        cls.agent = create_agent(unique_email("tag-dash-agent")).name
        cls.member = create_agent(unique_email("tag-dash-member")).name
        cls.customer = create_contact("Tag Customer", unique_email("tag-dash"))
        # so no ticket below is Administrator's first, which would get a tag
        make_ticket()

    def setUp(self) -> None:
        self.suffix = frappe.generate_hash(length=6)
        self.team = make_team(f"Tag Team {self.suffix}", [self.member]).name

    def test_top_tags_count_each_tag_of_a_ticket(self) -> None:
        billing, refund = self.tag("billing"), self.tag("refund")
        make_tagged_ticket(self.team, "2031-03-10 10:00:00", billing, refund)
        make_tagged_ticket(self.team, "2031-03-11 10:00:00", billing)
        make_tagged_ticket(self.team, "2031-03-11 11:00:00")

        top_tags = self.get_charts("2031-03-10", "2031-03-11")["top_tags"]["data"]
        # ascending, so the chart draws the biggest bar on top
        self.assertEqual(
            top_tags, [{"tag": refund, "Tickets": 1}, {"tag": billing, "Tickets": 2}]
        )

    def test_date_range_includes_whole_first_and_last_day(self) -> None:
        billing = self.tag("billing")
        make_tagged_ticket(self.team, "2031-04-09 23:59:59", billing)
        make_tagged_ticket(self.team, "2031-04-10 00:00:00", billing)
        make_tagged_ticket(self.team, "2031-04-12 23:59:59", billing)
        make_tagged_ticket(self.team, "2031-04-13 00:00:00", billing)

        charts = self.get_charts("2031-04-10", "2031-04-12")
        self.assertEqual(self.top_tag_counts(charts), {billing: 2})

    def test_tag_trend_zero_fills_each_day(self) -> None:
        billing, refund = self.tag("billing"), self.tag("refund")
        make_tagged_ticket(self.team, "2031-05-01 09:00:00", billing)
        make_tagged_ticket(self.team, "2031-05-01 17:00:00", billing)
        make_tagged_ticket(self.team, "2031-05-03 09:00:00", refund)

        trend = self.get_charts("2031-05-01", "2031-05-03")["tag_trend"]
        self.assertEqual(
            trend["data"],
            [
                {"date": getdate("2031-05-01"), billing: 2, refund: 0},
                {"date": getdate("2031-05-03"), billing: 0, refund: 1},
            ],
        )
        self.assertEqual(
            [series["name"] for series in trend["series"]], [billing, refund]
        )

    def test_charts_keep_only_the_busiest_tags(self) -> None:
        # tag i sits on i + 1 tickets, so the ranking has no ties
        tags = [self.tag(f"t{index}") for index in range(11)]
        for index in range(11):
            make_tagged_ticket(self.team, "2031-06-01 10:00:00", *tags[index:])

        charts = self.get_charts("2031-06-01", "2031-06-01")
        top_tags = [row["tag"] for row in charts["top_tags"]["data"]]
        trend_tags = [series["name"] for series in charts["tag_trend"]["series"]]
        self.assertEqual(top_tags, tags[1:])
        self.assertEqual(trend_tags, tags[:5:-1])

    def test_untagged_tickets_give_empty_charts(self) -> None:
        make_tagged_ticket(self.team, "2031-07-01 10:00:00")

        charts = self.get_charts("2031-07-01", "2031-07-01")
        self.assertEqual(charts["top_tags"]["data"], [])
        self.assertEqual(charts["tag_trend"]["data"], [])
        self.assertEqual(charts["tag_trend"]["series"], [])

    def test_other_teams_tickets_are_not_counted(self) -> None:
        billing = self.tag("billing")
        other_team = make_team(f"Other Tag Team {self.suffix}", [self.member]).name
        make_tagged_ticket(self.team, "2031-08-01 10:00:00", billing)
        make_tagged_ticket(other_team, "2031-08-01 10:00:00", billing)

        charts = self.get_charts("2031-08-01", "2031-08-01")
        self.assertEqual(self.top_tag_counts(charts), {billing: 1})

    def test_deleted_ticket_and_removed_tag_are_not_counted(self) -> None:
        billing = self.tag("billing")
        make_tagged_ticket(self.team, "2031-09-01 10:00:00", billing)
        deleted = make_tagged_ticket(self.team, "2031-09-01 10:00:00", billing)
        untagged = make_tagged_ticket(self.team, "2031-09-01 10:00:00", billing)
        frappe.delete_doc("HD Ticket", deleted.name, force=True)
        untagged.remove_tag(billing)

        charts = self.get_charts("2031-09-01", "2031-09-01")
        self.assertEqual(self.top_tag_counts(charts), {billing: 1})

    def test_agent_sees_tags_of_own_tickets_only(self) -> None:
        billing = self.tag("billing")
        mine = make_tagged_ticket(self.team, "2031-10-01 10:00:00", billing)
        make_tagged_ticket(self.team, "2031-10-01 10:00:00", billing)
        frappe.db.set_value("HD Ticket", mine.name, "_assign", json.dumps([self.agent]))

        filters = {
            "from_date": "2031-10-01",
            "to_date": "2031-10-01",
            "agent": self.agent,
        }
        with self.set_user(self.agent):
            charts = self.by_key(get_dashboard_data("tags", filters))
        self.assertEqual(self.top_tag_counts(charts), {billing: 1})

    def test_agent_cannot_view_team_or_org_tag_charts(self) -> None:
        with self.set_user(self.agent):
            with self.assertRaises(frappe.PermissionError):
                get_dashboard_data("tags", {"team": self.team, "agent": self.agent})
            with self.assertRaises(frappe.PermissionError):
                get_dashboard_data("tags", {})

    def test_customer_cannot_view_tag_charts(self) -> None:
        with self.set_user(self.customer["user"]):
            with self.assertRaises(frappe.PermissionError):
                get_dashboard_data("tags", {"agent": self.customer["user"]})

    def tag(self, label: str) -> str:
        return f"{label}-{self.suffix}"

    def get_charts(self, from_date: str, to_date: str) -> dict[str, dict]:
        """Tag charts for this test's team, as the manager sees them."""
        filters = {"from_date": from_date, "to_date": to_date, "team": self.team}
        with self.set_user(self.manager):
            return self.by_key(get_dashboard_data("tags", filters))

    @staticmethod
    def by_key(charts: list[dict]) -> dict[str, dict]:
        return {chart["key"]: chart for chart in charts}

    @staticmethod
    def top_tag_counts(charts: dict[str, dict]) -> dict[str, int]:
        return {row["tag"]: row["Tickets"] for row in charts["top_tags"]["data"]}
