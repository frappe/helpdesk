import frappe


def execute():
    frappe.db.delete("HD View", {"dt": "HD Agent"})
    frappe.db.delete("HD View", {"dt": "HD Team"})
