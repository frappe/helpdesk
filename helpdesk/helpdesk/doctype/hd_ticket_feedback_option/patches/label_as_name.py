import frappe


def execute():
	doctype = "HD Ticket Feedback Option"
	options = frappe.get_list(
		doctype, fields=["name", "label"], limit_page_length=99999
	)
	for opt in options:
		if opt.name != opt.label:
			frappe.rename_doc(doctype, opt.name, opt.label, ignore_if_exists=True)
