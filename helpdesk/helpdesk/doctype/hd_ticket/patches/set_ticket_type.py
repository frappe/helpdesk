import frappe


def execute():
	QBTicket = frappe.qb.DocType("HD Ticket")
	(
		frappe.qb.update(QBTicket)
		.set(QBTicket.ticket_type, "Unspecified")
		.where(QBTicket.ticket_type.isnull())
		.run()
	)
