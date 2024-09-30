import frappe


@frappe.whitelist()
def get_category(category):
    category_doc = frappe.get_doc("HD Article Category", category)
    return category_doc
