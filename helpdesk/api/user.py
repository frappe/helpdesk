import frappe


@frappe.whitelist()
def get_all():
	QBUser = frappe.qb.DocType("User")
	query = frappe.qb.from_(QBUser).select(
		QBUser.email,
		QBUser.full_name,
		QBUser.name,
		QBUser.user_image,
		QBUser.username,
	)
	return query.run(as_dict=True)
