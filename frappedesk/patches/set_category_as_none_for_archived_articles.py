import frappe


def execute():
	articles = frappe.get_all(
		"Article", filters={"status": "Archived"}, fields=["name", "category"], limit=9999
	)
	for article in articles:
		if article.category != None:
			frappe.db.set_value("Article", article.name, "category", None)
			frappe.db.commit()
