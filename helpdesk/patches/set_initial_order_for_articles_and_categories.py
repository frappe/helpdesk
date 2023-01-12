import frappe


def execute():
	catagories = frappe.get_all("Category", filters={"is_group": 1}, fields=["name"])
	for index, category in enumerate(catagories):
		sub_categories = frappe.get_all(
			"Category", filters={"parent_category": category["name"]}, order_by="modified desc"
		)
		for index_2, sub_category in enumerate(sub_categories):
			sub_category_doc = frappe.get_doc("Category", sub_category)
			if hasattr(sub_category_doc, "order"):
				sub_category_doc.order = index_2
				sub_category_doc.save()
		category_doc = frappe.get_doc("Category", category)
		if hasattr(category_doc, "order"):
			category_doc.order = index
			category_doc.save()

	for category in frappe.get_all("Category", fields=["name"]):
		articles = frappe.get_all(
			"Article", filters={"category": category["name"]}, order_by="modified desc"
		)
		for index, article in enumerate(articles):
			article_doc = frappe.get_doc("Article", article)
			if hasattr(article_doc, "order"):
				article_doc.order = index
				article_doc.save()
