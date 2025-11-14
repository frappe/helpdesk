# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class HDAgent(Document):
    def before_save(self):
        old_doc = self.get_doc_before_save()
        if old_doc and old_doc.agent_name != self.agent_name:
            if self.agent_name:
                agent_name = self.agent_name.split()
                frappe.set_value(
                    "User",
                    self.user,
                    {
                        "first_name": agent_name[0],
                        "last_name": " ".join(agent_name[1:]),
                    },
                )
            else:
                self.agent_name = frappe.get_value("User", self.user, "full_name")

        if old_doc and old_doc.user_image != self.user_image:
            frappe.set_value("User", self.user, "user_image", self.user_image)

        if self.name == self.user:
            return

        self.name = self.user
        self.set_user_roles()

    def set_user_roles(self):
        user = frappe.get_doc("User", self.user)
        for role in ["Agent"]:
            user.append("roles", {"role": role})
        user.save(ignore_permissions=True)


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


@frappe.whitelist()
def get_agent():
    if frappe.db.exists("HD Agent", {"user": frappe.session.user}):
        return frappe.get_doc("HD Agent", {"user": frappe.session.user})
    else:
        user = frappe.get_doc("User", frappe.session.user)
        agent = frappe.get_doc(
            {
                "doctype": "HD Agent",
                "ID": frappe.session.user,
                "user": frappe.session.user,
                "agent_name": user.full_name,
                "user_image": user.user_image,
            }
        ).insert(ignore_permissions=True)
        return agent
