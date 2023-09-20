import frappe


@frappe.whitelist()
def clear(user: str = None, ticket: str | int = None, comment: str = None):
	"""
	Mark notifications as read. No arguments will clear all notifications for `user`.

	:param user: User to clear notifications for
	:param ticket: Ticket to clear notifications for
	:param comment: Comment to clear notifications for
	"""
	QBNotification = frappe.qb.DocType("HD notification")
	user = user or frappe.session.user
	q = (
		frappe.qb.update(QBNotification)
		.where(QBNotification.user_to == user)
		.set(QBNotification.read, True)
	)
	if ticket:
		q = q.where(QBNotification.reference_ticket == ticket)
	if comment:
		q = q.where(QBNotification.reference_comment == comment)
	q.run()
