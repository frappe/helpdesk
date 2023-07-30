import frappe

from helpdesk.consts import DEFAULT_TICKET_TYPE


def execute():
	add_fallback()
	set_ticket_type()


def add_fallback():
	if frappe.db.exists("HD Ticket Type", DEFAULT_TICKET_TYPE):
		return
	d = frappe.new_doc("HD Ticket Type")
	d.is_system = True
	d.name = DEFAULT_TICKET_TYPE
	d.save()


def set_ticket_type():
	QBTicket = frappe.qb.DocType("HD Ticket")
	(
		frappe.qb.update(QBTicket)
		.set(QBTicket.ticket_type, DEFAULT_TICKET_TYPE)
		.where(QBTicket.ticket_type.isnull())
		.run()
	)
