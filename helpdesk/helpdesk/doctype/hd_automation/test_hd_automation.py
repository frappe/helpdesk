# Copyright (c) 2024, Frappe Technologies and Contributors
# See license.txt

import frappe
import json
from frappe.tests import IntegrationTestCase, UnitTestCase


# On IntegrationTestCase, the doctype test records and all
# link-field test record depdendencies are recursively loaded
# Use these module variables to add/remove to/from that list
EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]


class TestHDAutomation(UnitTestCase):
	"""
	Unit tests for HDAutomation.
	Use this class for testing individual functions and methods.
	"""

	def test_assign_group(self):
		user1 = frappe.new_doc(
			"User", first_name="Agent 1", email="agent1@example.com"
		).insert()
		agent1 = frappe.new_doc("HD Agent", user=user1.name)
		billing_team = frappe.new_doc(
			"HD Team", team_name="Billing", users=[{"user": user1.name}]
		)

		automation = frappe.new_doc(
			"HD Automation",
			enabled=1,
			title="Set group automatically",
			event="On ticket creation",
			rule=json.dumps(
				{
					"condition": "and",
					"rules": [
						{"field": "subject", "operator": "like", "value": "%billing%"},
					],
				}
			),
		).insert()

		ticket = frappe.new_doc("HD Ticket", subject="my billing is not working").insert()

		self.assertEqual(ticket.agent_group, "Billing")


class TestHDAutomation(IntegrationTestCase):
	"""
	Integration tests for HDAutomation.
	Use this class for testing interactions between multiple components.
	"""

	pass
