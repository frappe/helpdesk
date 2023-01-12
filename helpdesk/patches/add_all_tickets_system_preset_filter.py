import frappe


def execute():
	preset_filter_doc = frappe.get_doc(
		{
			"doctype": "Helpdesk Preset Filter",
			"title": "All Tickets",
			"reference_doctype": "Ticket",
			"filters": [],
		}
	)
	preset_filter_doc.insert()
