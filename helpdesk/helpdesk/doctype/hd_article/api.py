import frappe


@frappe.whitelist()
def get_article(name: str):
	article = frappe.get_doc("HD Article", name).as_dict()
	author = frappe.get_cached_doc("User", article["author"])
	sub_category = frappe.get_cached_doc("HD Article Category", article["category"])
	category = frappe.get_cached_doc(
		"HD Article Category", sub_category.parent_category
	)

	return {
		**article,
		"author": author,
		"category": category,
		"sub_category": sub_category,
	}
