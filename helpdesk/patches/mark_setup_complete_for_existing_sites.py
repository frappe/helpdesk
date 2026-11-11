import frappe

from helpdesk.consts import WELCOME_TICKET_SUBJECT


def execute():
    """A site already in use never sees the first-run setup."""
    in_use = frappe.db.exists(
        "HD Ticket", {"subject": ["!=", WELCOME_TICKET_SUBJECT]}
    ) or frappe.db.count("Email Account")
    if in_use:
        frappe.db.set_single_value("HD Settings", "setup_complete", 1)
