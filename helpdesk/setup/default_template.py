import frappe


def create_default_template():
	if frappe.db.exists("HD Ticket Template", "Default"):
		return

	template = frappe.new_doc("HD Ticket Template")
	template.template_name = "Default"
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
