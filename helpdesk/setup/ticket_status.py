import frappe

DEFAULT_TICKET_STATUS = ["Open", "Replied", "Resolved", "Closed"]
DT_NAME = "HD Ticket Status"

def create_default_ticket_status():
	for status in DEFAULT_TICKET_STATUS:
		if frappe.db.exists(DT_NAME, status):
			return

		d = frappe.new_doc(DT_NAME)
		d.name = status
		d.is_default = status == "Open"
		d.save()
