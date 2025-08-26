import frappe


def execute():
    frappe.db.set_single_value(
        "HD Settings",
        "enable_reply_email_to_agent",
        1,
    )
    frappe.db.set_single_value(
        "HD Settings",
        "enable_reply_email_via_agent",
        1,
    )
