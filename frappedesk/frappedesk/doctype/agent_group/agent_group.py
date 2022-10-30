# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.exceptions import DoesNotExistError


class AgentGroup(Document):
	# TODO: handle document rename
	def after_insert(self):
		self.create_assignment_rule()

	def on_trash(self):
		try:
			rule = self.get_assignment_rule()
			if rule:
				rule.delete(ignore_permissions=True)
		except DoesNotExistError:
			# TODO: Log this error
			pass

	def create_assignment_rule(self):
		rule_doc = frappe.new_doc("Assignment Rule")
		rule_doc.name = f"Support Rotation - {self.name}"
		rule_doc.document_type = "Ticket"
		rule_doc.assign_condition = f"status == 'Open' and agent_group == '{self.name}'"

		for day in [
			"Monday",
			"Tuesday",
			"Wednesday",
			"Thursday",
			"Friday",
			"Saturday",
			"Sunday",
		]:
			day_doc = frappe.get_doc({"doctype": "Assignment Rule Day", "day": day})
			rule_doc.append("assignment_days", day_doc)

		rule_doc.save(ignore_permissions=True)

	def get_assignment_rule(self):
		return get_assignement_rule_by_group_name(self.name)


def get_assignement_rule_by_group_name(name):
	rule_doc = None
	try:
		rule_doc = frappe.get_last_doc(
			"Assignment Rule",
			filters=[
				[
					"Assignment Rule",
					"assign_condition",
					"=",
					f"status == 'Open' and agent_group == '{name}'",
				],
			],
		)
	except DoesNotExistError:
		pass

	return rule_doc
