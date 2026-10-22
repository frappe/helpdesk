import frappe
from frappe.permissions import add_permission, update_permission_property


def execute():
    if frappe.db.exists("Role", "Agent Manager"):
        add_permission("Email Domain", "Agent Manager", ptype="read")
        update_permission_property("Email Domain", "Agent Manager", 0, "read", 1)
