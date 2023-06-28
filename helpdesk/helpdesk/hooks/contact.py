import frappe


class Contact:
	@staticmethod
	def get_list_filters(query):
		QBContact = frappe.qb.DocType("Contact")
		QBEmail = frappe.qb.DocType("Contact Email")
		QBPhone = frappe.qb.DocType("Contact Phone")
		QBLink = frappe.qb.DocType("Dynamic Link")

		query = (
			query.select(QBContact.first_name)
			.select(QBContact.last_name)
			.left_join(QBEmail)
			.on(QBEmail.parent == QBContact.name)
			.select(QBEmail.email_id)
			.left_join(QBPhone)
			.on(QBPhone.parent == QBContact.name)
			.select(QBPhone.phone)
			.left_join(QBLink)
			.on(QBLink.parent == QBContact.name)
			.select(QBLink.link_name)
		)

		return query
