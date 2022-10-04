import frappe


def get_context(context):
	context.categories = frappe.get_all(
		"Category", fields=["name", "description", "category_name"]
	)
	context.articles = frappe.get_all("Article")
	return context


@frappe.whitelist(allow_guest=True)
def get_category_website_route(category):
	return frappe.get_doc("Category", category)
