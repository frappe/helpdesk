import frappe


def execute():
	settings = frappe.get_doc("Helpdesk Settings")
	if frappe.db.exists("Ticket Type", "Question"):
		settings.default_ticket_type = "Question"
		settings.save()
