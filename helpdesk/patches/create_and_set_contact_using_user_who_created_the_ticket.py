import frappe


def execute():
	for ticket in frappe.db.get_all(
		"HD Ticket",
		filters={"contact": "", "owner": ["!=", "Administrator"]},
		fields=["name", "owner"],
	):
		user_doc = frappe.get_doc("User", ticket.owner)
		new_contact_doc = frappe.get_doc(
			doctype="Contact",
			email_id=user_doc.email,
			full_name=user_doc.full_name,
			first_name=user_doc.first_name,
			last_name=user_doc.last_name,
			user=user_doc.name,
		)
		new_contact_doc.append("email_ids", {"email_id": user_doc.email, "is_primary": True})
		new_contact_doc.insert()

		ticket_doc = frappe.get_doc("HD Ticket", ticket.name)
		ticket_doc.contact = new_contact_doc.name
		ticket_doc.save()
