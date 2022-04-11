# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class Agent(Document):
	def before_save(self):
		user = frappe.get_doc("User", self.user)
		self.name = user.name

		user.role_profile_name = "Agent"
		user.save()

@frappe.whitelist()
def create_agent(first_name, last_name, email, signature, team):
	if frappe.db.exists("User", email):
		user = frappe.get_doc("User", email)
	else:
		user = frappe.get_doc({
			"doctype": "User",
			"first_name": first_name,
			"last_name": last_name,
			"email": email,
			"email_signature": signature
		}).insert()
		
		user.send_welcome_mail_to_user()

	return frappe.get_doc({
		"doctype": "Agent",
		"user": user.name,
		"group": team
	}).insert()

	return agent