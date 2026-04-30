import frappe


def execute():
	if not frappe.db.exists("HD Ticket Template", "Default"):
		return

	template = frappe.get_doc("HD Ticket Template", "Default")
	existing = [r.fieldname for r in template.fields]

	if "total_hours" not in existing:
		template.append("fields", {
			"fieldname": "total_hours",
			"hide_from_customer": 1,
		})
		template.save(ignore_permissions=True)
		frappe.db.commit()
