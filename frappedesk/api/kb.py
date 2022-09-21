import frappe
from frappe.model.rename_doc import rename_doc

@frappe.whitelist()
def update_category(old_category_name, new_category_name, new_description):
	category_doc = frappe.get_doc("Category", old_category_name)
	category_doc.category_name = new_category_name
	category_doc.description = new_description
	category_doc.save()

	if (old_category_name != new_category_name):
		rename_doc("Category", old_category_name, new_category_name)


@frappe.whitelist()
def delete_category(category):
	artiles = frappe.get_all("Article", filters={"category": ["=", category]}, pluck="name")
	if len(artiles) != 0:
		raise Exception("Cannot delete category with articles")
	else:
		frappe.delete_doc("Category", category)