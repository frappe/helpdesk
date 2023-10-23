import frappe


def execute():
	for t in frappe.get_all("HD Ticket"):
		try:
			c = frappe.get_last_doc(
				"Communication",
				filters={
					"reference_doctype": "HD Ticket",
					"reference_name": t.name,
					"sent_or_received": "Sent",
				},
				order_by="creation asc",
			)
		except frappe.DoesNotExistError:
			continue
		ticket = frappe.get_doc("HD Ticket", t.name)
		modified = ticket.modified
		ticket.first_responded_on = c.creation
		ticket.save()
		ticket.db_set("modified", modified, update_modified=False)
		frappe.db.commit()
