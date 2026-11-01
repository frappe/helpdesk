import frappe
from frappe.utils.html_utils import sanitize_html


def execute():
    ticket = frappe.db.get_value(
        "HD Ticket",
        {"subject": "Welcome to Helpdesk"},
        ["name", "description"],
        as_dict=True,
    )
    if not ticket:
        return

    frappe.db.set_value(
        "HD Ticket",
        ticket.name,
        "description",
        sanitize_html(ticket.description, linkify=True),
        update_modified=False,
    )
