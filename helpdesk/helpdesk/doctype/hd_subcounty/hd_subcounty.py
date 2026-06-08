# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class HDSubcounty(Document):
	pass


@frappe.whitelist()
def get_subcounty_name(subcounty_name, county):
	"""Get the full document name from subcounty_name and county"""
	result = frappe.db.get_value(
		"HD Subcounty",
		{"subcounty_name": subcounty_name, "county": county},
		"name"
	)
	return result
