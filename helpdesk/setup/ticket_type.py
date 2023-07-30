import frappe

from helpdesk.consts import DEFAULT_TICKET_TYPE

DT = "HD Ticket Type"
TICKET_TYPES = ["Question", "Bug", "Incident"]


def create_fallback_ticket_type():
	if frappe.db.exists(DT, DEFAULT_TICKET_TYPE):
		return

	d = frappe.new_doc(DT)
	d.name = DEFAULT_TICKET_TYPE
	d.is_system = True
	d.save()


def create_ootb_ticket_types():
	for ticket_type in TICKET_TYPES:
		if frappe.db.exists(DT, ticket_type):
			return

		d = frappe.new_doc(DT)
		d.name = ticket_type
		d.is_system = False
		d.save()
