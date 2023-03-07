import frappe


def execute():
	if not frappe.db.exists("Ticket Template", "Default"):
		return

	t = frappe.get_doc("Ticket Template", "Default")
	t.append(
		"fields",
		{
			"label": "Type",
			"fieldname": "ticket_type",
			"fieldtype": "Link",
			"options": "Ticket Type",
			"reqd": False,
		},
	)

	t.save()
	frappe.db.commit()
