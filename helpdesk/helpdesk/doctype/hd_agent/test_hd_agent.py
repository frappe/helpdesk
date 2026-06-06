# Copyright (c) 2022, Frappe Technologies and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from helpdesk.api.agent import get_my_availability, set_my_availability
from helpdesk.helpdesk.doctype.hd_agent.hd_agent import update_agent_role
from helpdesk.test_utils import make_agent, make_team, make_ticket


def _set_agent_availability(user: str, availability: str | None):
    agent = frappe.db.get_value("HD Agent", {"user": user}, "name")
    frappe.db.set_value("HD Agent", agent, "availability", availability)


class TestHDAgent(FrappeTestCase):
    test_user = "test_user@test.com"

    def setUp(self):
<<<<<<< HEAD
        if not frappe.db.exists("User", self.test_user):
            frappe.get_doc(
                {
                    "doctype": "User",
                    "email": self.test_user,
                    "first_name": "Test User",
                    "send_welcome_email": 0,
                }
            ).insert(ignore_permissions=True)
        else:
            frappe.get_doc("User", self.test_user)

        frappe.get_doc("User", self.test_user).remove_roles(
            "System Manager", "Agent Manager"
        )

    def tearDown(self):
        frappe.set_user("Administrator")
        frappe.delete_doc("User", self.test_user, force=True, ignore_missing=True)
=======
        make_agent(self.test_user, first_name="Test User")
>>>>>>> 779d4a06 (test: add testcases for agent status)

    # a new agent defaults to the Active-category status (looked up, not hardcoded)
    def test_new_agent_defaults_to_active_status(self):
        agent = make_agent("defaults_active@test.com", first_name="Defaults Active")

        self.assertEqual(
            frappe.db.get_value("HD Agent", agent, "availability"), "Active"
        )

    def test_unauthorized_role_update(self):
        frappe.set_user(self.test_user)

        frappe.flags.in_test = False

        try:
            with self.assertRaises(frappe.PermissionError):
                update_agent_role(self.test_user, "System Manager")
        finally:
            frappe.flags.in_test = True

    # check if agent can update their own availability successfully
    def test_set_my_availability_persists_value(self):
        frappe.set_user(self.test_user)

        result = set_my_availability("Away")

        self.assertEqual(result["availability"], "Away")
        stored = frappe.db.get_value(
            "HD Agent",
            {"user": self.test_user},
            ["availability", "availability_changed_on"],
            as_dict=True,
        )
        self.assertEqual(stored.availability, "Away")
        self.assertIsNotNone(stored.availability_changed_on)

    # an availability that is not a configured HD Agent Status is rejected
    def test_set_my_availability_rejects_invalid_status(self):
        frappe.set_user(self.test_user)

        with self.assertRaises(frappe.ValidationError):
            set_my_availability("Not A Status")

    # get_my_availability returns the agent's status, when it changed, and options
    def test_get_my_availability_returns_status_and_options(self):
        frappe.set_user(self.test_user)
        set_my_availability("Away")

        result = get_my_availability()

        self.assertEqual(result["availability"], "Away")
        self.assertIsNotNone(result["availability_changed_on"])
        self.assertIn("Away", result["options"])

    def _make_assignment_rule(self, team_name: str, members: list[str], rule: str):
        team = make_team(team_name, members)
        assignment_rule = frappe.get_doc("Assignment Rule", team.assignment_rule)
        if assignment_rule.rule != rule:
            assignment_rule.rule = rule
            assignment_rule.save(ignore_permissions=True)
            team.reload()
            team.save(ignore_permissions=True)
            assignment_rule.reload()
        assignment_rule.last_user = None
        return assignment_rule

    # Round Robin: away user is skipped, next user in list is picked
    def test_round_robin_skips_away_agent(self):
        active_user = make_agent("rr_active@test.com", first_name="RR Active")
        away_user = make_agent("rr_away@test.com", first_name="RR Away")
        _set_agent_availability(active_user, "Active")
        _set_agent_availability(away_user, "Away")

        assignment_rule = self._make_assignment_rule(
            "Test AR Round Robin", [away_user, active_user], "Round Robin"
        )

        picked = assignment_rule.get_user(make_ticket(subject="RR skip away"))

        self.assertEqual(picked, active_user)

    # Away agent is preferred over an Unavailable one if no Active is available
    def test_round_robin_prefers_away_over_unavailable(self):
        away_user = make_agent("rr_away_over_unavail@test.com", first_name="RR Away")
        unavailable_user = make_agent(
            "rr_unavailable@test.com", first_name="RR Unavailable"
        )
        _set_agent_availability(away_user, "Away")
        _set_agent_availability(unavailable_user, "Unavailable")

        assignment_rule = self._make_assignment_rule(
            "Test AR Away Over Unavailable",
            [unavailable_user, away_user],
            "Round Robin",
        )

        picked = assignment_rule.get_user(
            make_ticket(subject="RR away over unavailable")
        )

        self.assertEqual(picked, away_user)

    # A custom status under the Away category is tiered as away, not active
    def test_round_robin_uses_category_not_status_name(self):
        if not frappe.db.exists("HD Agent Status", "Lunch"):
            frappe.get_doc(
                {
                    "doctype": "HD Agent Status",
                    "agent_status": "Lunch",
                    "category": "Away",
                    "enable": 1,
                    "status_order": 5,
                }
            ).insert()

        active_user = make_agent("cat_active@test.com", first_name="Cat Active")
        lunch_user = make_agent("cat_lunch@test.com", first_name="Cat Lunch")
        _set_agent_availability(active_user, "Active")
        _set_agent_availability(lunch_user, "Lunch")

        assignment_rule = self._make_assignment_rule(
            "Test AR Category Away", [lunch_user, active_user], "Round Robin"
        )

        picked = assignment_rule.get_user(make_ticket(subject="RR category away"))

        self.assertEqual(picked, active_user)

    # Load Balancing: away user is excluded from the candidate pool
    def test_load_balancing_skips_away_agent(self):
        active_user = make_agent("lb_active@test.com", first_name="LB Active")
        away_user = make_agent("lb_away@test.com", first_name="LB Away")
        _set_agent_availability(active_user, "Active")
        _set_agent_availability(away_user, "Away")

        assignment_rule = self._make_assignment_rule(
            "Test AR Load Balancing", [away_user, active_user], "Load Balancing"
        )

        picked = assignment_rule.get_user(make_ticket(subject="LB skip away"))

        self.assertEqual(picked, active_user)

    # Weighted Distribution: away user is removed from the weighted pool
    def test_weighted_distribution_skips_away_agent(self):
        active_user = make_agent("wd_active@test.com", first_name="WD Active")
        away_user = make_agent("wd_away@test.com", first_name="WD Away")
        _set_agent_availability(active_user, "Active")
        _set_agent_availability(away_user, "Away")

        assignment_rule = self._make_assignment_rule(
            "Test AR Weighted", [away_user, active_user], "Weighted Distribution"
        )

        picked_users = {
            assignment_rule.get_user(make_ticket(subject=f"WD skip away {i}"))
            for i in range(5)
        }

        self.assertEqual(picked_users, {active_user})

    def test_assignment_rule_falls_back_when_all_agents_are_away(self):
        """If every member is Away, still assign rather than leave the ticket orphaned."""
        first_user = make_agent("ar_all_away_1@test.com", first_name="All Away 1")
        second_user = make_agent("ar_all_away_2@test.com", first_name="All Away 2")
        _set_agent_availability(first_user, "Away")
        _set_agent_availability(second_user, "Away")

        team = make_team("Test AR All Away", [first_user, second_user])
        assignment_rule = frappe.get_doc("Assignment Rule", team.assignment_rule)
        assignment_rule.last_user = None

        picked = assignment_rule.get_user(make_ticket(subject="AR all away"))

        self.assertIn(picked, {first_user, second_user})

    # Based on field: test to check if assignment rule ignores away status and assigns as per document field value
    def test_based_on_field_ignores_away_filter(self):
        away_user = make_agent("bf_away@test.com", first_name="BF Away")
        _set_agent_availability(away_user, "Away")

        assignment_rule = self._make_assignment_rule(
            "Test AR Based on Field", [away_user], "Round Robin"
        )
        assignment_rule.rule = "Based on Field"
        assignment_rule.field = "raised_by"
        assignment_rule.save(ignore_permissions=True)

        ticket = make_ticket(subject="BF ignore away", raised_by=away_user)

        self.assertEqual(assignment_rule.get_user(ticket), away_user)

    # Manual assignment: backend must allow assigning an Away agent
    def test_manual_assignment_allows_away_agent(self):
        away_user = make_agent("manual_away@test.com", first_name="Manual Away")
        _set_agent_availability(away_user, "Away")

        ticket = make_ticket(subject="Manual to away agent")
        ticket.assign_agent(away_user)

        assignees = frappe.get_all(
            "ToDo",
            filters={
                "reference_type": "HD Ticket",
                "reference_name": ticket.name,
                "status": "Open",
            },
            pluck="allocated_to",
        )
        self.assertIn(away_user, assignees)

    def tearDown(self):
        frappe.set_user("Administrator")
