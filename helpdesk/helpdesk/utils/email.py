import frappe
from frappe.query_builder import DocType, Query


def query_get_one(q: Query) -> dict:
	r = q.run(as_dict=True)

	if len(r) != 1:
		return

	return r.pop()


def default_outgoing_email_account():
	QBEmailAccount = DocType("Email Account")

	r = (
		frappe.qb.from_(QBEmailAccount)
		.select(QBEmailAccount.star)
		.where(QBEmailAccount.default_outgoing == 1)
		.limit(1)
	)

	return query_get_one(r)


def default_ticket_outgoing_email_account():
	QBEmailAccount = DocType("Email Account")
	QBImapFolder = DocType("IMAP Folder")

	r = (
		frappe.qb.from_(QBEmailAccount)
		.select(QBEmailAccount.star)
		.where(QBEmailAccount.default_outgoing == 1)
		.inner_join(QBImapFolder)
		.on(QBImapFolder.parent == QBEmailAccount.name)
		.where(QBImapFolder.append_to == "HD Ticket")
		.limit(1)
	)

	return query_get_one(r)
