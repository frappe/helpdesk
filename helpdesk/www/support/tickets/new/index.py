from hashlib import new
from re import sub
import frappe

@frappe.whitelist()
def create_ticket(subject, type, description):
	new_ticket = frappe.new_doc("Ticket")

	new_ticket.subject = subject
	new_ticket.ticket_type = type
	new_ticket.description = description
	new_ticket.via_customer_portal = True
	
	new_ticket.insert(ignore_permissions=True)

	return new_ticket