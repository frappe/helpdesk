# Copyright (c) 2022, Frappe Technologies and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from helpdesk.test_utils import make_agent, make_team, make_ticket


class TestHDTeam(FrappeTestCase):

    def test_assignment_rule_created_on_team_insert(self):
        team = make_team("Test AR Creation")
        self.assertTrue(team.assignment_rule)
        self.assertTrue(frappe.db.exists("Assignment Rule", team.assignment_rule))

    def test_conditions_set_on_creation(self):
        team = make_team("Test Conditions Creation")
        ar = frappe.get_doc("Assignment Rule", team.assignment_rule)

        self.assertEqual(
            ar.assign_condition,
            f"status == 'Open' and agent_group == '{team.name}'",
        )
        self.assertIn(team.name, ar.assign_condition_json)

        self.assertEqual(ar.unassign_condition, f"agent_group != '{team.name}'")
        self.assertIn(team.name, ar.unassign_condition_json)
        self.assertIn("!=", ar.unassign_condition_json)

    def test_conditions_updated_on_rename(self):
        team = make_team("Test Conditions Rename Old")
        ar_name = team.assignment_rule
        new_name = "Test Conditions Rename New"

        frappe.rename_doc("HD Team", team.name, new_name)

        ar = frappe.get_doc("Assignment Rule", ar_name)
        self.assertEqual(
            ar.assign_condition,
            f"status == 'Open' and agent_group == '{new_name}'",
        )
        self.assertIn(new_name, ar.assign_condition_json)
        self.assertEqual(ar.unassign_condition, f"agent_group != '{new_name}'")
        self.assertIn(new_name, ar.unassign_condition_json)

    def test_round_robin_users_synced(self):
        agent1 = make_agent("rr_sync_1@example.com")
        agent2 = make_agent("rr_sync_2@example.com")
        team = make_team("Test RR Sync", [agent1, agent2])

        # Both members should be in AR users
        ar = frappe.get_doc("Assignment Rule", team.assignment_rule)
        ar_users = {u.user for u in ar.users}
        self.assertEqual(ar_users, {agent1, agent2})

        # Remove agent2 from team
        team.reload()
        team.users = [u for u in team.users if u.user != agent2]
        team.save(ignore_permissions=True)

        ar.reload()
        ar_users = {u.user for u in ar.users}
        self.assertIn(agent1, ar_users)
        self.assertNotIn(agent2, ar_users)

    def test_weighted_users_synced(self):
        agent1 = make_agent("wd_sync_1@example.com")
        agent2 = make_agent("wd_sync_2@example.com")
        agent3 = make_agent("wd_sync_3@example.com")
        team = make_team("Test Weighted Sync", [agent1, agent2])

        # Switch AR to Weighted Distribution
        ar = frappe.get_doc("Assignment Rule", team.assignment_rule)
        ar.rule = "Weighted Distribution"
        ar.save(ignore_permissions=True)

        # Trigger sync by saving team
        team.reload()
        team.save(ignore_permissions=True)

        ar.reload()
        ar_weighted = {u.user for u in ar.weighted_users}
        self.assertEqual(ar_weighted, {agent1, agent2})

        # Set agent1's weight directly in DB — no hooks triggered
        row = next(r for r in ar.weighted_users if r.user == agent1)
        frappe.db.set_value("Assignment Rule User", row.name, "weight", 5)

        # Add agent3 — triggers resync
        team.reload()
        team.append("users", {"user": agent3})
        team.save(ignore_permissions=True)

        ar.reload()
        preserved = next((r for r in ar.weighted_users if r.user == agent1), None)
        self.assertIsNotNone(preserved)
        self.assertEqual(preserved.weight, 5)

        added = next((r for r in ar.weighted_users if r.user == agent3), None)
        self.assertIsNotNone(added)
        self.assertEqual(added.weight, 1)

        # Remove agent2 — triggers resync
        team.reload()
        team.users = [u for u in team.users if u.user != agent2]
        team.save(ignore_permissions=True)

        ar.reload()
        ar_weighted = {u.user for u in ar.weighted_users}
        self.assertIn(agent1, ar_weighted)
        self.assertIn(agent3, ar_weighted)
        self.assertNotIn(agent2, ar_weighted)
