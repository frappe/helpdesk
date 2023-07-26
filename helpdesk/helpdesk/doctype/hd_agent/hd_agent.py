# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class HDAgent(Document):
	def before_save(self):
		if self.name == self.user:
			return

		self.name = self.user
		self.set_user_roles()

	def set_user_roles(self):
		user = frappe.get_doc("User", self.user)

		for role in ["Agent"]:
			user.append("roles", {"role": role})

		user.save()

	def on_update(self):
		if self.has_value_changed("is_active"):
			if not self.is_active:
				self.remove_from_support_rotations()
			else:
				self.add_to_support_rotations()

		if self.has_value_changed("groups") and self.is_active:
			previous = self.get_doc_before_save()
			if previous:
				for group in previous.groups:
					if not next(
						(g for g in self.groups if g.team == group.team),
						None,
					):
						self.remove_from_support_rotations(group.team)

			self.add_to_support_rotations()

	def on_trash(self):
		self.remove_from_support_rotations()

	def add_to_support_rotations(self, group=None):
		"""
		Add the hd_agent to the support rotation for the given group or all groups
		the hd_agent belongs to if hd_agent already added to the support roatation
		for a group, skip

		:param str group: Team name, defaults to None.
		"""
		rule_docs = []
		if not group:
			# Add the hd_agent to the base support rotation

			rule_docs.append(
				frappe.get_doc(
					"Assignment Rule",
					frappe.get_doc("HD Settings").get_base_support_rotation(),
				)
			)

			# Add the hd_agent to the support rotation for each group they belong to
			if self.groups:
				for group in self.groups:
					try:
						team_assignment_rule = frappe.get_doc(
							"HD Team", group.team
						).get_assignment_rule()
						rule_docs.append(
							frappe.get_doc(
								"Assignment Rule",
								team_assignment_rule,
							)
						)
					except frappe.DoesNotExistError:
						frappe.throw(
							frappe._(
								"Assignment Rule for HD Team {0} does not exist"
							).format(group.team)
						)
		else:
			# check if the group is in self.groups
			if next(
				(group for group in self.groups if group["group_name"] == group), None
			):
				rule_docs.append(
					frappe.get_doc(
						"Assignment Rule",
						frappe.get_doc("HD Team", group).get_assignment_rule(),
					)
				)
			else:
				frappe.throw(
					frappe._(
						"Agent {0} does not belong to team {1}".format(
							self.agent_name, group
						)
					)
				)

		for rule_doc in rule_docs:
			skip = False
			if rule_doc:
				if rule_doc.users and len(rule_doc.users) > 0:
					for user in rule_doc.users:
						if (
							user.user == self.user
						):  # if the user is already in the rule, skip
							skip = True
							break
				if skip:
					continue

				user_doc = frappe.get_doc(
					{"doctype": "Assignment Rule User", "user": self.user}
				)
				rule_doc.append("users", user_doc)
				rule_doc.disabled = False  # enable the rule if it is disabled
				rule_doc.save(ignore_permissions=True)

	def remove_from_support_rotations(self, group=None):
		rule_docs = []

		if group:
			# remove the hd_agent from the support rotation for the given group
			rule_docs.append(
				frappe.get_doc(
					"Assignment Rule",
					frappe.get_doc("HD Team", group).get_assignment_rule(),
				)
			)

		else:
			# Remove the hd_agent from the base support rotation
			rule_docs.append(
				frappe.get_doc(
					"Assignment Rule",
					frappe.get_doc("HD Settings").get_base_support_rotation(),
				)
			)

			# Remove the hd_agent from the support rotation for each group they belong to
			for group in self.groups:
				rule_docs.append(
					frappe.get_doc(
						"Assignment Rule",
						frappe.get_doc("HD Team", group.team).get_assignment_rule(),
					)
				)

		for rule_doc in rule_docs:
			if rule_doc.users and len(rule_doc.users) > 0:
				for user in rule_doc.users:
					if user.user == self.user:
						if len(rule_doc.users) == 1:
							rule_doc.disabled = (
								True  # disable the rule if there are no users left
							)
						rule_doc.remove(user)
						rule_doc.save()

	def in_group(self, group):
		"""
		Check if agent is in the given group
		"""
		if self.groups:
			return next((g for g in self.groups if g.team == group), False)

		return False


@frappe.whitelist()
def create_hd_agent(first_name, last_name, email, signature, team):
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

	return frappe.get_doc(
		{"doctype": "HD Agent", "user": user.name, "group": team}
	).insert()
