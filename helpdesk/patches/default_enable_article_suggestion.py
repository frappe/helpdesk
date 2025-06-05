import frappe


def execute():
    frappe.db.set_single_value("HD Settings", "show_suggested_articles", 1)
