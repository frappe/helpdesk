# Copyright (c) 2022, Frappe Technologies and Contributors
# See license.txt

import json

import frappe
from frappe.tests.utils import FrappeTestCase

from helpdesk.test_utils import make_agent, make_team


class TestHDTeam(FrappeTestCase):
    def test_assignment_rule_creation(self):
        team = make_team("Test Team")
        self.assertTrue(team.assignment_rule)
        ar_name = f"{team.name} - Support Rotation"
        self.assertTrue(frappe.db.exists("Assignment Rule", ar_name))

    def test_team_rename_updates_assignment_rule(self):
        team = make_team("Test Team Rename")
        old_rule_name = team.assignment_rule
        new_team_name = "Renamed Test Team"
        frappe.rename_doc("HD Team", team.name, new_team_name)
        team = frappe.get_doc("HD Team", new_team_name)
        updated_rule = frappe.get_doc("Assignment Rule", old_rule_name)
        expected_condition = f"status == 'Open' and agent_group == '{new_team_name}'"
        self.assertEqual(updated_rule.assign_condition, expected_condition)

    def test_team_agent_sync_with_assignment_rule(self):
        agent1 = make_agent("testagent1@example.com")
        agent2 = make_agent("testagent2@example.com")
        team = make_team("Test Team Sync", [agent1, agent2])

        rule_doc = frappe.get_doc("Assignment Rule", team.assignment_rule)

        assignment_rule_users = [user.user for user in rule_doc.users]
        agents_in_team = [agent.user for agent in team.users]
        self.assertEqual(json.dumps(assignment_rule_users), json.dumps(agents_in_team))
