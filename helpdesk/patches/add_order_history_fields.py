# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and Contributors
# License: AGPLv3. See LICENSE

import frappe


def execute():
	"""
	Add custom_order_history field to HD Ticket
	"""
	
	# Add Tab Break for Order Details
	if not frappe.db.exists("Custom Field", {"dt": "HD Ticket", "fieldname": "custom_order_details_tab"}):
		frappe.get_doc({
			"doctype": "Custom Field",
			"dt": "HD Ticket",
			"label": "Order Details",
			"fieldname": "custom_order_details_tab",
			"fieldtype": "Tab Break",
			"insert_after": "meta_tab"
		}).insert(ignore_permissions=True)
	
	# Add custom_order_history child table field
	if not frappe.db.exists("Custom Field", {"dt": "HD Ticket", "fieldname": "custom_order_history"}):
		frappe.get_doc({
			"doctype": "Custom Field",
			"dt": "HD Ticket",
			"label": "Order History",
			"fieldname": "custom_order_history",
			"fieldtype": "Table",
			"options": "HD Ticket Order Item",
			"insert_after": "custom_order_details_tab"
		}).insert(ignore_permissions=True)
	
	frappe.db.commit()

