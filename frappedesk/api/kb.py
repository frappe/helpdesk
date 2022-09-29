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

@frappe.whitelist()
def check_if_category_name_exists_outside_current_hierarchy(category_name, parent_category=None):
	doc = {"doctype": "Category", "category_name": category_name}

	if parent_category:
		doc["parent_category"] = parent_category
	else:
		doc["is_group"] = False

	return (frappe.db.exists(doc) is not None)