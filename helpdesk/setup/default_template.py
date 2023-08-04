import frappe

from helpdesk.consts import DEFAULT_TICKET_TEMPLATE


def create_default_template():
	if frappe.db.exists("HD Ticket Template", DEFAULT_TICKET_TEMPLATE):
		return

	template = frappe.new_doc("HD Ticket Template")
	template.template_name = DEFAULT_TICKET_TEMPLATE
	template.append(
		"fields",
		{
			"label": "Type",
			"fieldname": "ticket_type",
			"fieldtype": "Link",
			"options": "HD Ticket Type",
			"reqd": False,
		},
	)
	template.insert()
