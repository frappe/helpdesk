import frappe

DT = "HD Ticket Type"
TICKET_TYPES = ["Question", "Bug", "Incident"]


def create_system_ticket_type():
	DN = "Uncategorised"

	if frappe.db.exists(DT, DN):
		return

	d = frappe.new_doc(DT)
	d.name = DN
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
