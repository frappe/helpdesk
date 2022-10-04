# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Agent(Document):
	def before_save(self):
		self.name = self.user
		self.set_user_roles()

	def set_user_roles(self):
		user = frappe.get_doc("User", self.user)
		for role in ["Agent", "System Manager"]:
			user.append("roles", {"role": role})
		user.save()

	def after_insert(self):
		rule_doc = get_assignment_rule()
		user_doc = frappe.get_doc({"doctype": "Assignment Rule User", "user": self.user})
		rule_doc.append("users", user_doc)
		rule_doc.save(ignore_permissions=True)

	def on_trash(self):
		rule_doc = get_assignment_rule()
		for user in rule_doc.get("users"):
			if user.user == self.name:
				rule_doc.remove(user)
		rule_doc.save(ignore_permissions=True)


def get_assignment_rule():
	rules = frappe.get_all(
		"Assignment Rule", filters={"document_type": "Ticket", "disabled": False}
	)
	if rules:
		return frappe.get_doc("Assignment Rule", rules[0])
	else:
		frappe.throw("No assignment rule found for Tickets!!")


@frappe.whitelist()
def create_agent(first_name, last_name, email, signature, team):
	if frappe.db.exists("User", email):
		user = frappe.get_doc("User", email)
	else:
		user = frappe.get_doc(
			{
				"doctype": "User",
				"first_name": first_name,
				"last_name": last_name,
				"email": email,
				"email_signature": signature,
			}
		).insert()

		user.send_welcome_mail_to_user()

	return frappe.get_doc({"doctype": "Agent", "user": user.name, "group": team}).insert()
