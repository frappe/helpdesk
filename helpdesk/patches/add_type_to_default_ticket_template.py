import frappe


def execute():
	if not frappe.db.exists("HD Ticket Template", "Default"):
		return

	t = frappe.get_doc("HD Ticket Template", "Default")
	t.append(
		"fields",
		{
			"label": "Type",
			"fieldname": "ticket_type",
			"fieldtype": "Link",
			"options": "HD Ticket Type",
			"reqd": False,
		},
	)

	t.save()
	frappe.db.commit()
