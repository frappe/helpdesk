import frappe


def execute():
	settings = frappe.get_doc("HD Settings")
	if frappe.db.exists("HD Ticket Type", "Question"):
		settings.default_ticket_type = "Question"
		settings.save()
