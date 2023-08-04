import frappe

from helpdesk.consts import DEFAULT_TICKET_TEMPLATE


def create_default_template():
	doc = {
		"doctype": "HD Ticket Template",
		"template_name": DEFAULT_TICKET_TEMPLATE,
	}
	frappe.get_doc(doc).save()
