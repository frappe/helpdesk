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

	def on_update(self):
		if self.has_value_changed("is_active"):
			if not self.is_active:
				self.remove_from_support_rotations()
			else:
				self.add_to_support_rotations()

		if self.has_value_changed("group") and self.is_active:
			previous = self.get_doc_before_save()
			if previous:
				self.remove_from_support_rotations(group=previous.get("group"))
			if self.group:
				self.add_to_support_rotations()

	def on_trash(self):
		self.remove_from_support_rotations()

	def add_to_support_rotations(self):
		rule_docs = []
		rule_docs.append(frappe.get_doc("Assignment Rule", "Support Rotation"))
		if self.group:
			rule_docs.append(frappe.get_doc("Agent Group", self.group).get_assignment_rule())

		for rule_doc in rule_docs:
			skip = False
			if rule_doc:
				if rule_doc.users and len(rule_doc.users) > 0:
					for user in rule_doc.users:
						if user.user == self.name:  # if the user is already in the rule, skip
							skip = True
							break
				if skip:
					continue

				user_doc = frappe.get_doc({"doctype": "Assignment Rule User", "user": self.user})
				rule_doc.append("users", user_doc)
				rule_doc.save(ignore_permissions=True)

	def remove_from_support_rotations(self, group=None):
		rule_docs = []
		if group:
			rule_docs.append(frappe.get_doc("Agent Group", group).get_assignment_rule())
		else:
			rules = frappe.get_all(
				"Assignment Rule",
				filters={
					"user": self.user,
					"name": ["like", "%Support Rotation%"],
					"document_type": "Ticket",
				},
				fields=["name"],
			)
			for rule in rules:
				rule_docs.append(frappe.get_doc("Assignment Rule", rule.name))
		for rule_doc in rule_docs:
			if rule_doc.users and len(rule_doc.users) > 0:
				for user in rule_doc.users:
					if user.user == self.user:
						rule_doc.remove(user)
						rule_doc.save()


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
