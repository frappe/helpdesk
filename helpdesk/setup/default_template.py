import frappe

from helpdesk.consts import DEFAULT_TICKET_TEMPLATE


def create_default_template():
    if frappe.db.exists("HD Ticket Template", DEFAULT_TICKET_TEMPLATE):
        return
    doc = {
        "doctype": "HD Ticket Template",
        "template_name": DEFAULT_TICKET_TEMPLATE,
    }
    frappe.get_doc(doc).save()
