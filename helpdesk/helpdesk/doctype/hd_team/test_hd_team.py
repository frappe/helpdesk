# Copyright (c) 2022, Frappe Technologies and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from helpdesk.test_utils import make_agent, make_team, make_ticket


class TestHDTeam(FrappeTestCase):

    # --- Assignment Rule creation ---

    def test_assignment_rule_created_on_team_insert(self):
        team = make_team("Test AR Creation")
        self.assertTrue(team.assignment_rule)
        self.assertTrue(frappe.db.exists("Assignment Rule", team.assignment_rule))

    # --- assign_condition ---

    def test_assign_condition_set_on_creation(self):
        team = make_team("Test Assign Condition")
        ar = frappe.get_doc("Assignment Rule", team.assignment_rule)
        self.assertEqual(
            ar.assign_condition,
            f"status == 'Open' and agent_group == '{team.name}'",
        )

    def test_assign_condition_updated_on_rename(self):
        team = make_team("Test Assign Rename Old")
        ar_name = team.assignment_rule
        new_name = "Test Assign Rename New"
        frappe.rename_doc("HD Team", team.name, new_name)
        ar = frappe.get_doc("Assignment Rule", ar_name)
        self.assertEqual(
            ar.assign_condition,
            f"status == 'Open' and agent_group == '{new_name}'",
        )

    # --- unassign_condition ---

    def test_unassign_condition_set_on_creation(self):
        team = make_team("Test Unassign Condition")
        ar = frappe.get_doc("Assignment Rule", team.assignment_rule)
        self.assertEqual(ar.unassign_condition, f"agent_group != '{team.name}'")
        self.assertIn("!=", ar.unassign_condition_json)
        self.assertIn(team.name, ar.unassign_condition_json)

    def test_unassign_condition_updated_on_rename(self):
        team = make_team("Test Unassign Rename Old")
        ar_name = team.assignment_rule
        new_name = "Test Unassign Rename New"
        frappe.rename_doc("HD Team", team.name, new_name)
        ar = frappe.get_doc("Assignment Rule", ar_name)
        self.assertEqual(ar.unassign_condition, f"agent_group != '{new_name}'")
        self.assertIn(new_name, ar.unassign_condition_json)

    # --- Team → AR: users sync ---

    def test_team_members_synced_to_ar_users(self):
        agent1 = make_agent("sync_users_1@example.com")
        agent2 = make_agent("sync_users_2@example.com")
        team = make_team("Test AR Users Sync", [agent1, agent2])

        ar = frappe.get_doc("Assignment Rule", team.assignment_rule)
        ar_users = {u.user for u in ar.users}
        self.assertEqual(ar_users, {agent1, agent2})

    def test_adding_member_adds_to_ar_users(self):
        agent1 = make_agent("add_user_1@example.com")
        agent2 = make_agent("add_user_2@example.com")
        team = make_team("Test Add Member AR", [agent1])

        team.reload()
        team.append("users", {"user": agent2})
        team.save(ignore_permissions=True)

        ar = frappe.get_doc("Assignment Rule", team.assignment_rule)
        ar_users = {u.user for u in ar.users}
        self.assertIn(agent1, ar_users)
        self.assertIn(agent2, ar_users)

    def test_removing_member_removes_from_ar_users(self):
        agent1 = make_agent("remove_user_1@example.com")
        agent2 = make_agent("remove_user_2@example.com")
        team = make_team("Test Remove Member AR", [agent1, agent2])

        team.reload()
        team.users = [u for u in team.users if u.user != agent2]
        team.save(ignore_permissions=True)

        ar = frappe.get_doc("Assignment Rule", team.assignment_rule)
        ar_users = {u.user for u in ar.users}
        self.assertIn(agent1, ar_users)
        self.assertNotIn(agent2, ar_users)

    # --- Team → AR: weighted_users sync ---

    def test_team_members_synced_to_ar_weighted_users(self):
        agent1 = make_agent("sync_weighted_1@example.com")
        agent2 = make_agent("sync_weighted_2@example.com")
        team = make_team("Test AR Weighted Sync", [agent1, agent2])

        ar = frappe.get_doc("Assignment Rule", team.assignment_rule)
        ar_weighted = {u.user for u in ar.weighted_users}
        self.assertEqual(ar_weighted, {agent1, agent2})

    def test_new_member_gets_default_weight_one(self):
        agent = make_agent("weight_default@example.com")
        team = make_team("Test Weight Default", [agent])

        ar = frappe.get_doc("Assignment Rule", team.assignment_rule)
        row = next((r for r in ar.weighted_users if r.user == agent), None)
        self.assertIsNotNone(row)
        self.assertEqual(row.weight, 1)

    def test_existing_weight_preserved_on_resync(self):
        agent1 = make_agent("weight_preserve_1@example.com")
        agent2 = make_agent("weight_preserve_2@example.com")
        team = make_team("Test Weight Preserve", [agent1])

        # Set agent1's weight to 5 directly in the DB — no save hooks triggered
        ar = frappe.get_doc("Assignment Rule", team.assignment_rule)
        weighted_row = next(r for r in ar.weighted_users if r.user == agent1)
        frappe.db.set_value("Assignment Rule User", weighted_row.name, "weight", 5)

        # Add agent2 to team — triggers full resync
        team.reload()
        team.append("users", {"user": agent2})
        team.save(ignore_permissions=True)

        ar.reload()
        preserved = next((r for r in ar.weighted_users if r.user == agent1), None)
        self.assertIsNotNone(preserved)
        self.assertEqual(preserved.weight, 5)

        added = next((r for r in ar.weighted_users if r.user == agent2), None)
        self.assertIsNotNone(added)
        self.assertEqual(added.weight, 1)

    def test_removing_member_removes_from_ar_weighted_users(self):
        agent1 = make_agent("remove_weighted_1@example.com")
        agent2 = make_agent("remove_weighted_2@example.com")
        team = make_team("Test Remove Weighted", [agent1, agent2])

        team.reload()
        team.users = [u for u in team.users if u.user != agent2]
        team.save(ignore_permissions=True)

        ar = frappe.get_doc("Assignment Rule", team.assignment_rule)
        ar_weighted = {u.user for u in ar.weighted_users}
        self.assertIn(agent1, ar_weighted)
        self.assertNotIn(agent2, ar_weighted)

    # --- AR disabled/enabled state ---

    def test_ar_enabled_when_team_has_members(self):
        agent = make_agent("ar_enable@example.com")
        team = make_team("Test AR Enable", [agent])

        ar = frappe.get_doc("Assignment Rule", team.assignment_rule)
        self.assertFalse(ar.disabled)

    def test_ar_disabled_when_team_is_empty(self):
        agent = make_agent("ar_disable@example.com")
        team = make_team("Test AR Disable", [agent])

        team.reload()
        team.users = []
        team.save(ignore_permissions=True)

        ar = frappe.get_doc("Assignment Rule", team.assignment_rule)
        self.assertTrue(ar.disabled)

    # --- AR → HD Team sync ---

    def test_adding_user_to_ar_users_syncs_to_team(self):
        agent1 = make_agent("ar_to_team_1@example.com")
        agent2 = make_agent("ar_to_team_2@example.com")
        team = make_team("Test AR to Team Users", [agent1])

        ar = frappe.get_doc("Assignment Rule", team.assignment_rule)
        ar.append("users", {"user": agent2})
        ar.save(ignore_permissions=True)

        team.reload()
        team_members = {u.user for u in team.users}
        self.assertIn(agent1, team_members)
        self.assertIn(agent2, team_members)

    def test_adding_user_to_ar_weighted_users_syncs_to_team(self):
        agent1 = make_agent("ar_to_team_w1@example.com")
        agent2 = make_agent("ar_to_team_w2@example.com")
        team = make_team("Test AR to Team Weighted", [agent1])

        ar = frappe.get_doc("Assignment Rule", team.assignment_rule)
        ar.append("weighted_users", {"user": agent2, "weight": 2})
        ar.save(ignore_permissions=True)

        team.reload()
        team_members = {u.user for u in team.users}
        self.assertIn(agent1, team_members)
        self.assertIn(agent2, team_members)

    def test_removing_user_from_ar_users_syncs_to_team(self):
        agent1 = make_agent("ar_remove_1@example.com")
        agent2 = make_agent("ar_remove_2@example.com")
        team = make_team("Test AR Remove User Sync", [agent1, agent2])

        ar = frappe.get_doc("Assignment Rule", team.assignment_rule)
        ar.users = [u for u in ar.users if u.user != agent2]
        ar.weighted_users = [u for u in ar.weighted_users if u.user != agent2]
        ar.save(ignore_permissions=True)

        team.reload()
        team_members = {u.user for u in team.users}
        self.assertIn(agent1, team_members)
        self.assertNotIn(agent2, team_members)

    # --- Ticket assignment ---

    def test_ticket_assigned_to_team_agent(self):
        agent = make_agent("ticket_agent@example.com")
        team = make_team("Test Ticket Assignment", [agent])

        ar = frappe.get_doc("Assignment Rule", team.assignment_rule)
        self.assertFalse(ar.disabled)

        ticket = make_ticket(
            subject="Test Team Assignment Ticket",
            agent_group=team.name,
        )

        from frappe.automation.doctype.assignment_rule.assignment_rule import (
            apply as apply_assignment_rules,
        )

        apply_assignment_rules(ticket)
        ticket.reload()

        assigned = frappe.parse_json(ticket._assign or "[]")
        self.assertIn(agent, assigned)
