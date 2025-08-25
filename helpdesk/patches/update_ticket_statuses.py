import frappe

from helpdesk.setup.install import add_default_status


def execute():
    add_default_status()

    if frappe.db.get_single_value("HD Settings", "auto_update_status"):
        frappe.db.set_single_value("HD Settings", "update_status_to", "Replied")

    frappe.db.set_single_value("HD Settings", "default_ticket_status", "Open")
    frappe.db.set_single_value("HD Settings", "ticket_reopen_status", "Open")
    if frappe.db.get_single_value("HD Settings", "auto_close_tickets"):
        frappe.db.set_single_value("HD Settings", "auto_close_status", "Replied")

    frappe.db.sql("DELETE FROM `tabHD Pause Service Level Agreement On Status`")
    frappe.db.sql("DELETE FROM `tabHD Service Level Agreement Fulfilled On Status`")
