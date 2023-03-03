import frappe

from frappe.model.base_document import get_controller


def execute():
	doc = {
		"doctype": "FD Preset Filter",
		"title": "All Open Tickets",
		"reference_doctype": "Ticket",
	}

	if frappe.db.exists(doc):
		return

	preset_controller = get_controller("FD Preset Filter")
	filter_open = preset_controller.get_status_filter("Open")

	filter = frappe.get_doc(
		{
			**doc,
			"filters": [filter_open],
		}
	)

	filter.insert()
	frappe.db.commit()
