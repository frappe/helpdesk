import frappe


def execute():
	if not frappe.db.exists("HD Ticket Template", "Default"):
		return

	template = frappe.get_doc("HD Ticket Template", "Default")
	if "estimated_hours" in [r.fieldname for r in template.fields]:
		return

	template.append("fields", {
		"fieldname": "estimated_hours",
		"hide_from_customer": 1,
	})
	template.save(ignore_permissions=True)
	frappe.db.commit()
