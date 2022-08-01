from frappedesk.setup.install import add_default_ticket_types
import frappe

def execute():
	categories = frappe.get_all("Category", filters={"is_group": ["=", True]}, order_by="modified desc")
	for index, category in enumerate(categories):
		category_doc = frappe.get_doc("Category", category.name)
		category_doc.order = index
		category_doc.save()
		# all the sub_category & article ordering will be done when the parent category is saved