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


@frappe.whitelist()
def update_agent_role(user, new_role):
    """
    Update the role of the user to Agent
    """

    user_doc = frappe.get_doc("User", user)

    if new_role == "Manager":
        user_doc.append_roles("Agent Manager", "System Manager")
    if new_role == "Agent":
        user_doc.append_roles("Agent")
        if "Agent Manager" in frappe.get_roles(user_doc.name):
            user_doc.remove_roles("Agent Manager", "System Manager")

    user_doc.save()
