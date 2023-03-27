from frappedesk.frappedesk.doctype.hd_ticket.hd_ticket import (
	set_descritption_from_communication,
)
import frappe


def execute():
	for ticket in frappe.get_all(
		"HD Ticket", filters={"via_customer_portal": False}, fields=["name"]
	):
		if frappe.db.exists("Communication", {"reference_name": ticket.name}):
			communication_doc = frappe.get_doc("Communication", {"reference_name": ticket.name})
			ticket_doc = frappe.get_doc("HD Ticket", ticket.name)
			ticket_doc.description = communication_doc.content
			ticket_doc.save()
