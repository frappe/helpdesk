# Copyright (c) 2022, Frappe Technologies and Contributors
# See license.txt

from unittest.mock import patch

import frappe
from frappe.client import set_value as client_set_value
from frappe.tests.utils import FrappeTestCase

from helpdesk.api.auth import get_user
from helpdesk.helpdesk.doctype.hd_agent.hd_agent import update_agent_role
from helpdesk.test_utils import (
    make_agent,
    make_team,
    make_ticket,
    set_agent_availability,
    set_agent_status_enabled,
)


class TestHDAgent(FrappeTestCase):
    test_user = "test_user@test.com"

    def setUp(self):
        # Frappe only resets the session user per class, so tests that switch user
        # leak into every later one. Reset both ends, as the rest of the suite does.
        frappe.set_user("Administrator")
        make_agent(self.test_user, first_name="Test User")
        # Rollback is per-class, so availability leaks between tests. Reset to a
        # known status or "did this change?" assertions depend on test order.
        set_agent_availability(self.test_user, "Active")

    def tearDown(self):
        frappe.set_user("Administrator")

    def _disable_status(self, status: str):
        set_agent_status_enabled(status, 0)
        self.addCleanup(set_agent_status_enabled, status, 1)

    def _set_availability_as(self, user: str, agent: str, availability: str):
        """Submit the payload agentStatus.ts sends, as `user`."""
        frappe.set_user(user)
        return client_set_value(
            doctype="HD Agent",
            name=agent,
            fieldname="availability",
            value=availability,
        )

    # a new agent defaults to the Active-category status (looked up, not hardcoded)
    def test_new_agent_defaults_to_active_status(self):
        agent = make_agent("defaults_active@test.com", first_name="Defaults Active")

        self.assertEqual(
            frappe.db.get_value("HD Agent", agent, "availability"), "Active"
        )

    def test_unauthorized_role_update(self):
        frappe.set_user(self.test_user)

        with self.assertRaises(frappe.PermissionError):
            update_agent_role(self.test_user, "System Manager")

    # the frontend now writes this straight through frappe.client.set_value, so a
    # plain agent must be able to save their own record without elevated rights
    def test_agent_can_set_own_availability(self):
        frappe.set_user(self.test_user)

        agent = frappe.get_doc("HD Agent", self.test_user)
        agent.availability = "Away"
        agent.save()

        stored = frappe.db.get_value(
            "HD Agent",
            {"user": self.test_user},
            ["availability", "availability_changed_on"],
            as_dict=True,
        )
        self.assertEqual(stored.availability, "Away")
        self.assertIsNotNone(stored.availability_changed_on)

    # the exact payload desk/src/stores/agentStatus.ts now submits
    def test_client_set_value_updates_availability(self):
        self._set_availability_as(self.test_user, self.test_user, "Away")

        self.assertEqual(
            frappe.db.get_value("HD Agent", self.test_user, "availability"), "Away"
        )

    # HD Agent grants the Agent role blanket write, so without the has_permission
    # hook any agent could flip a colleague's status through client.set_value
    def test_agent_cannot_set_another_agents_availability(self):
        other = make_agent("other_agent@test.com", first_name="Other Agent")

        with self.assertRaises(frappe.PermissionError):
            self._set_availability_as(self.test_user, other, "Away")

        self.assertEqual(
            frappe.db.get_value("HD Agent", other, "availability"), "Active"
        )

    # managers still administer everyone — the Agents settings page depends on it
    def test_manager_can_set_another_agents_availability(self):
        other = make_agent("managed_agent@test.com", first_name="Managed Agent")
        manager = make_agent("agent_manager@test.com", first_name="Agent Manager")
        frappe.get_doc("User", manager).add_roles("Agent Manager")

        self._set_availability_as(manager, other, "Away")

        self.assertEqual(frappe.db.get_value("HD Agent", other, "availability"), "Away")

    # reads stay open — presence dots and assignment pickers list every agent
    def test_agent_can_still_read_another_agent(self):
        other = make_agent("readable_agent@test.com", first_name="Readable Agent")
        frappe.set_user(self.test_user)

        self.assertTrue(frappe.has_permission("HD Agent", "read", doc=other))
        self.assertFalse(frappe.has_permission("HD Agent", "write", doc=other))

    # an availability that is not a configured HD Agent Status is rejected
    def test_availability_rejects_unknown_status(self):
        with self.assertRaises(frappe.ValidationError):
            set_agent_availability(self.test_user, "Not A Status")

    # a status that exists but is disabled is rejected too — the Link field alone
    # does not filter on `enable`, so the controller has to
    def test_availability_rejects_disabled_status(self):
        self._disable_status("Unavailable")

        with self.assertRaises(frappe.ValidationError):
            set_agent_availability(self.test_user, "Unavailable")

    # an agent already on a since-disabled status can still save other fields
    def test_disabled_status_does_not_block_unrelated_save(self):
        agent = set_agent_availability(self.test_user, "Unavailable")
        self._disable_status("Unavailable")

        agent.reload()
        agent.is_active = 0
        agent.save(ignore_permissions=True)

        self.assertEqual(
            frappe.db.get_value("HD Agent", agent.name, "availability"), "Unavailable"
        )

    # every write path broadcasts, so the desk form and the portal stay in sync
    def test_availability_change_is_published(self):
        with patch(
            "helpdesk.helpdesk.doctype.hd_agent.hd_agent.publish_event"
        ) as publish:
            agent = set_agent_availability(self.test_user, "Away")

        publish.assert_called_once()
        event, kwargs = publish.call_args[0][0], publish.call_args[1]
        self.assertEqual(event, "agent_availability_updated")
        self.assertEqual(kwargs["data"]["agent"], agent.name)
        self.assertEqual(kwargs["data"]["availability"], "Away")

    def test_save_without_availability_change_is_not_published(self):
        set_agent_availability(self.test_user, "Away")
        agent = frappe.get_doc("HD Agent", {"user": self.test_user})

        with patch(
            "helpdesk.helpdesk.doctype.hd_agent.hd_agent.publish_event"
        ) as publish:
            agent.is_active = 0
            agent.save(ignore_permissions=True)

        publish.assert_not_called()

    # the session payload (auth.get_user) carries the agent's current status, so
    # the frontend seeds availability without a dedicated round-trip
    def test_get_user_includes_availability(self):
        set_agent_availability(self.test_user, "Away")
        frappe.set_user(self.test_user)

        result = get_user()

        self.assertEqual(result["availability"], "Away")
        self.assertIsNotNone(result["availability_changed_on"])

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
        set_agent_availability(active_user, "Active")
        set_agent_availability(away_user, "Away")

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
        set_agent_availability(away_user, "Away")
        set_agent_availability(unavailable_user, "Unavailable")

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
        set_agent_availability(active_user, "Active")
        set_agent_availability(lunch_user, "Lunch")

        assignment_rule = self._make_assignment_rule(
            "Test AR Category Away", [lunch_user, active_user], "Round Robin"
        )

        picked = assignment_rule.get_user(make_ticket(subject="RR category away"))

        self.assertEqual(picked, active_user)

    # Load Balancing: away user is excluded from the candidate pool
    def test_load_balancing_skips_away_agent(self):
        active_user = make_agent("lb_active@test.com", first_name="LB Active")
        away_user = make_agent("lb_away@test.com", first_name="LB Away")
        set_agent_availability(active_user, "Active")
        set_agent_availability(away_user, "Away")

        assignment_rule = self._make_assignment_rule(
            "Test AR Load Balancing", [away_user, active_user], "Load Balancing"
        )

        picked = assignment_rule.get_user(make_ticket(subject="LB skip away"))

        self.assertEqual(picked, active_user)

    # Weighted Distribution: away user is removed from the weighted pool
    def test_weighted_distribution_skips_away_agent(self):
        active_user = make_agent("wd_active@test.com", first_name="WD Active")
        away_user = make_agent("wd_away@test.com", first_name="WD Away")
        set_agent_availability(active_user, "Active")
        set_agent_availability(away_user, "Away")

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
        set_agent_availability(first_user, "Away")
        set_agent_availability(second_user, "Away")

        team = make_team("Test AR All Away", [first_user, second_user])
        assignment_rule = frappe.get_doc("Assignment Rule", team.assignment_rule)
        assignment_rule.last_user = None

        picked = assignment_rule.get_user(make_ticket(subject="AR all away"))

        self.assertIn(picked, {first_user, second_user})

    # Based on field: test to check if assignment rule ignores away status and assigns as per document field value
    def test_based_on_field_ignores_away_filter(self):
        away_user = make_agent("bf_away@test.com", first_name="BF Away")
        set_agent_availability(away_user, "Away")

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
        set_agent_availability(away_user, "Away")

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
        # Delete the teams created here so their auto-created assignment rules (and
        # the cached Assignment Rule doctype-map) don't leak into other tests and
        # break ticket creation with a phantom "... - Support Rotation not found".
        for team in frappe.get_all(
            "HD Team", filters={"name": ["like", "Test AR%"]}, pluck="name"
        ):
            frappe.delete_doc("HD Team", team, force=True, ignore_permissions=True)
