import frappe


def execute():
	all_tickets = frappe.get_all("HD Ticket")
	for ticket in all_tickets:
		# TODO: use version to set status, type, priority, team changes
		pass
