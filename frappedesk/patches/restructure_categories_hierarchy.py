import frappe

def execute():
    group_categories = frappe.get_all("Category", filters={"is_group": ["=", "1"]}, pluck="name")
    for group_category in group_categories:
        sub_categories = frappe.get_all("Category", filters={"parent_category": ["=", group_category]}, pluck="name")
        for sub_category in sub_categories:
            sub_category_doc = frappe.get_doc("Category", sub_category)
            sub_category_doc.parent_category = None
            sub_category_doc.order = 0
            sub_category_doc.save()
        frappe.delete_doc("Category", group_category)
    sub_categories = frappe.get_all("Category", filters={"is_group": ["=", "0"]}, pluck="name")
    for index, sub_category in enumerate(sub_categories):
        sub_category_doc = frappe.get_doc("Category", sub_category)
        sub_category_doc.order = index + 1
        sub_category_doc.save()