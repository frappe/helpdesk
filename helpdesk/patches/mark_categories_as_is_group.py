import frappe


def execute():
	categories = frappe.get_all("Category", pluck="name")
	for category in categories:
		category_doc = frappe.get_doc("Category", category)
		category_doc.is_group = 1
		category_doc.save()
