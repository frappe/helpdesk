# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.exceptions import DoesNotExistError
from frappe.model.document import Document
from frappe.model.naming import append_number_if_name_exists


class HDTeam(Document):
	@frappe.whitelist()
	def rename_self(self, new_name: str):
		self.rename(new_name)

	def after_insert(self):
		self.create_assignment_rule()

	def after_rename(self, olddn, newdn, merge=False):
		# Update the condition for the linked assignment rule
		rule = self.get_assignment_rule()
		rule_doc = frappe.get_doc("Assignment Rule", rule)
		rule_doc.assign_condition = f"status == 'Open' and agent_group == '{newdn}'"
		rule_doc.save(ignore_permissions=True)

	def on_trash(self):

		# Deletes the assignment rule for this group
		try:
			rule = self.get_assignment_rule()
			if rule:
				self.assignment_rule = ""
				self.save()
				frappe.get_doc("Assignment Rule", rule).delete()
		except DoesNotExistError:
			# TODO: Log this error
			pass

	def create_assignment_rule(self):
		"""Creates the assignment rule for this group"""

		rule_doc = frappe.new_doc("Assignment Rule")
		rule_doc.name = append_number_if_name_exists(
			"Assignment Rule", f"{self.name} - Support Rotation"
		)
		rule_doc.document_type = "HD Ticket"
		rule_doc.assign_condition = f"status == 'Open' and agent_group == '{self.name}'"
		rule_doc.priority = 1
		rule_doc.disabled = True  # Disable the rule by default, when agents are added to the group, the rule will be enabled

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
		self.assignment_rule = rule_doc.name
		self.save(ignore_permissions=True)

	def get_assignment_rule(self):
		"""
		Returns the assignment rule for this group, if not found creates one
		and returns it
		"""
		if not self.assignment_rule:
			self.create_assignment_rule()

		return self.assignment_rule
