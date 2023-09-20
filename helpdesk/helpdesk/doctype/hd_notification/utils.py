import frappe


@frappe.whitelist()
def clear(user: str = None, ticket: str | int = None, comment: str = None):
	"""
	Mark notifications as read. No arguments will clear all notifications for `user`.

	:param user: User to clear notifications for. Defaults to current `user`
	:param ticket: Ticket to clear notifications for
	:param comment: Comment to clear notifications for
	"""
	user = user or frappe.session.user
	filters = {"user_to": user, "read": False}
	if ticket:
		filters["reference_ticket"] = ticket
	if comment:
		filters["reference_comment"] = comment
	for n in frappe.get_all("HD Notification", filters=filters):
		d = frappe.get_doc("HD Notification", n.name)
		d.read = True
		d.save()
