# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class Agent(Document):
	def before_save(self):
		user = frappe.get_doc("User", self.user)
		self.name = user.name

		role_profile = frappe.get_doc({
			"doctype": "Role Profile",
			"role_profile": "Agent"
		})
		user.append("role_profile", role_profile)

		if self.email != user.email:
			user.email = self.email
		if self.signature != user.email_signature:
			user.email_signature = self.signature

		user.save()
