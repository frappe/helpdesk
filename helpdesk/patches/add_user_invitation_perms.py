import frappe
from frappe.permissions import add_permission, update_permission_property


def execute():
    doctype = "User Invitation"
    if frappe.db.exists("Role", "Agent Manager"):
        add_permission(
            doctype, "Agent Manager", 0
        )  # add_permission grants read permission to the role
        for permission in ["create", "write"]:
            update_permission_property(doctype, "Agent Manager", 0, permission, 1)
