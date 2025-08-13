import frappe

from helpdesk.setup.install import add_default_status


def execute():
    add_default_status()

    frappe.db.delete(
        "HD Service Level Agreement Fulfilled On Status",
        {"status": ["in", ["Replied", "Closed", "Open"]]},
    )

    frappe.db.delete(
        "HD Pause Service Level Agreement On Status",
        {"status": ["in", ["Resolved", "Closed", "Open"]]},
    )
