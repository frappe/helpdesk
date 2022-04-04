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
		user.save()

@frappe.whitelist()
def create_agent(name, email, signature, team):
	user = frappe.new_doc({
		"doctype": "User",
		"first_name": name,
		"email": email,
		"email_signature": signature
	}).insert()

	user.send_welcome_mail_to_user()

	return frappe.new_doc({
		"doctype": "Agent",
		"user": user.name,
		"group": team
	}).insert()

