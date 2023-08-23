import frappe


def execute():
	QBTicket = frappe.qb.DocType("HD Ticket")
	frappe.qb.update(QBTicket).set(QBTicket.agreement_status, "Failed").where(
		QBTicket.agreement_status == "Overdue"
	).run()
