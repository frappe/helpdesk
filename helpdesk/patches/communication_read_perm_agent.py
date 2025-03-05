import frappe
from frappe.permissions import add_permission


def execute():
    if frappe.db.exists("Role", "Agent"):
        add_permission("Communication", "Agent", 0)
