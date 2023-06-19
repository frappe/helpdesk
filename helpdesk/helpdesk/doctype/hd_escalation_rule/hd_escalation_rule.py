# Copyright (c) 2023, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class HDEscalationRule(Document):
	def validate(self):
		self.validate_criterion()
		self.validate_duplicate()

	def validate_criterion(self):
		if not (self.priority or self.team):
			frappe.throw(_("At-least priority or team is required"))

	def validate_duplicate(self):
		is_duplicate = frappe.db.count(
			"HD Escalation Rule",
			filters={
				"name": ["!=", self.name],
				"priority": self.priority or "",
				"team": self.team or "",
			},
		)

		if is_duplicate:
			frappe.throw(_("Escalation rule already exists for this criterion"))
