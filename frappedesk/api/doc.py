import frappe


@frappe.whitelist()
def delete_items(items, doctype):
	for item in items:
		frappe.delete_doc(doctype, item)
# @frappe.whitelist()
# def delete_single_item(item, doctype):
# 	frappe.delete_doc(doctype, item)