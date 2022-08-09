import frappe

def execute():
    catagories = frappe.get_all("Category", filters={"is_group": 1}, fields=["name"])
    for index, category in enumerate(catagories):
        sub_categories = frappe.get_all("Category", filters={"parent_category": category['name']}, order_by="modified desc")
        for index_2, sub_category in enumerate(sub_categories):
            frappe.get_doc("Category", sub_category).db_set("order", index_2)
        frappe.get_doc("Category", category).db_set("order", index)

    for category in frappe.get_all("Category", fields=["name"]):
        articles = frappe.get_all("Article", filters={"category": category['name']}, order_by="modified desc")
        for index, article in enumerate(articles):
            frappe.get_doc("Article", article).db_set("order", index)