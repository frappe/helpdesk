import frappe

from helpdesk.setup.welcome_ticket import AUTHOR_EMAIl as WELCOME_TICKET_AUTHOR


def execute():
    """Sites already handling tickets skip the first-run setup. A site with only the welcome
    ticket, like a v2 site created before this patch but not yet used, still gets it."""
    welcome = frappe.db.count("HD Ticket", {"raised_by": WELCOME_TICKET_AUTHOR})
    if frappe.db.count("HD Ticket") > welcome:
        frappe.db.set_single_value("HD Settings", "setup_complete", 1)
