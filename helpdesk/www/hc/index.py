import frappe


def get_context(context):
	context.categories = frappe.get_all(
		"Category",
		fields=["name", "description", "thumbnail", "parent_category", "is_group"],
		filters={"parent_category": ["=", ""]},
	)
	context.articles = frappe.get_all("Article")
	return context


@frappe.whitelist(allow_guest=True)
def get_child_categories(category):
	child_categories = frappe.get_all(
		"Category",
		fields=["name", "description", "parent_category", "is_group"],
		filters={"parent_category": ["=", category]},
	)
	return child_categories


@frappe.whitelist(allow_guest=True)
def get_category_website_route(category):
	return frappe.get_doc("Category", category)
