import frappe


@frappe.whitelist()
def delete_items(items, doctype):
    for item in items:
        frappe.delete_doc(doctype, item)
