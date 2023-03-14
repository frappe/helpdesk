import frappe


def default_outgoing_email_account():
	filters = [
		["use_imap", "=", 1],
		["default_outgoing", "=", 1],
	]

	return frappe.get_last_doc(
		"Email Account",
		filters,
	)


def default_ticket_outgoing_email_account():
	filters = [
		["use_imap", "=", 1],
		["default_outgoing", "=", 1],
		["IMAP Folder", "append_to", "=", "Ticket"],
	]

	return frappe.get_last_doc(
		"Email Account",
		filters,
	)
