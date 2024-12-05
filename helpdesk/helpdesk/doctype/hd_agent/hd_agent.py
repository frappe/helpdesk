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

    @staticmethod
    def default_list_data():
        columns = [
            {
                "label": "Name",
                "key": "name",
                "width": "240px",
            },
            {
                "label": "Email",
                "key": "email",
                "width": "240px",
            },
            {
                "label": "Username",
                "key": "user.username",
                "width": "240px",
            },
            {
                "label": "Full Name",
                "key": "user.full_name",
                "width": "240px",
            },
        ]
        rows = [
            "name",
            "is_active",
            "user.full_name",
            "user.user_image",
            "user.email",
            "user.username",
            "modified",
            "creation",
        ]
        return {"columns": columns, "rows": rows}


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
