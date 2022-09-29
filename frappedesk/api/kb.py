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

@frappe.whitelist()
def insert_new_update_existing_categories(new_values, old_values):
	# TODO: optimize this

	# set idx values for all the new_values based on index
	for i in range(len(new_values)):
		new_values[i]["idx"] = i

	to_insert = [{key : val for key, val in c.items() if key != 'is_new'} for c in new_values if "is_new" in c]
	to_update = [c for c in new_values if "is_new" not in c]

	names_in_old_values = [c["name"] for c in old_values]
	names_in_new_values = [c["name"] if "name" in c else "" for c in new_values]
	
	to_delete = [c for c in names_in_old_values if c not in names_in_new_values]

	# validate and delete missing categories
	for category in to_delete:
		if frappe.db.exists("Category", {"name": category, "parent_category": category}):
			raise Exception("Cannot delete category with subcategories")
		elif frappe.db.exists("Article", {"category": category}):
			raise Exception("Cannot delete category with articles")
		else:
			frappe.delete_doc("Category", category)
	
	# create new categories if present
	for category in to_insert:
		doc = frappe.new_doc("Category")
		doc.update(category)
		doc.save()
	
	# update description & category_name
	for category in to_update:
		doc = frappe.get_doc("Category", category["name"])
		doc.update(category)
		doc.save()

		# update category name if changed
		if (category["category_name"] != category["name"]):
			frappe.rename_doc("Category", category["name"], category["category_name"])

	return