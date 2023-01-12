import frappe


def execute():
	all_tickets_with_feedback = frappe.get_all(
		"Ticket", filters={"feedback_submitted": True}
	)
	tickets_before_reload = []
	for ticket in all_tickets_with_feedback:
		ticket_doc = frappe.get_doc("Ticket", ticket.name)
		tickets_before_reload.append(
			{"name": ticket_doc.name, "satisfied": ticket_doc.satisfied}
		)

	frappe.reload_doc("Helpdesk", "doctype", "Ticket")

	for ticket in tickets_before_reload:
		ticket_doc = frappe.get_doc("Ticket", ticket["name"])
		ticket_doc.satisfaction_rating = (5 if ticket["satisfied"] else 1) * 0.2
		ticket_doc.save()
