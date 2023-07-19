import frappe


@frappe.whitelist()
def get_list_public():
	fields = ["name", "category_name", "icon"]
	categories = frappe.get_list(
		"HD Article Category", fields=fields, filters={"parent_category": ""}
	)
	for category in categories:
		sub_categories = frappe.get_list(
			"HD Article Category",
			filters={"parent_category": category.name},
			fields=fields,
		)
		category.sub_categories = sub_categories
	categories = filter(lambda x: len(x.sub_categories), categories)
	return categories
