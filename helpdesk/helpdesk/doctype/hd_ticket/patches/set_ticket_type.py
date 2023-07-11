import frappe

from helpdesk.consts import FALLBACK_TICKET_TYPE


def execute():
	QBTicket = frappe.qb.DocType("HD Ticket")
	(
		frappe.qb.update(QBTicket)
		.set(QBTicket.ticket_type, FALLBACK_TICKET_TYPE)
		.where(QBTicket.ticket_type.isnull())
		.run()
	)
