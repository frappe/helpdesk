from frappedesk.frappedesk.doctype.ticket_activity import log_ticket_activity
import frappe


def execute():
	all_tickets = frappe.get_all("Ticket")
	for ticket in all_tickets:
		# TODO: use version to set status, type, priority, team changes
		pass
