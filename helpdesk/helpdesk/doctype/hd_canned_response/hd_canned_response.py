# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class HDCannedResponse(Document):
	def validate(self):
		if self.shortcut:
			self.shortcut = self.shortcut.strip().lower()
			if not self.shortcut.startswith('/'):
				self.shortcut = '/' + self.shortcut

	def increment_usage(self):
		"""Increment usage count and update last used timestamp"""
		frappe.db.set_value(
			self.doctype,
			self.name,
			{
				"usage_count": self.usage_count + 1,
				"last_used": frappe.utils.now()
			}
		)


@frappe.whitelist()
def get_canned_responses(search_term=None, category=None):
	"""Get all active canned responses with optional filtering"""
	try:
		# Check if table exists
		if not frappe.db.table_exists("HD Canned Response"):
			return []

		filters = {"is_active": 1}

		if category:
			filters["category"] = category

		canned_responses = frappe.get_all(
			"HD Canned Response",
			filters=filters,
			fields=["name", "title", "shortcut", "category", "message", "usage_count"],
			order_by="usage_count desc, modified desc"
		)
	except Exception as e:
		frappe.log_error(f"Error fetching canned responses: {str(e)}")
		return []

	if search_term:
		search_term = search_term.lower()
		canned_responses = [
			cr for cr in canned_responses
			if search_term in cr.title.lower()
			or (cr.shortcut and search_term in cr.shortcut.lower())
			or search_term in cr.message.lower()
		]

	return canned_responses


@frappe.whitelist()
def use_canned_response(name):
	"""Mark a canned response as used"""
	try:
		doc = frappe.get_doc("HD Canned Response", name)
		doc.increment_usage()
		return doc.message
	except Exception as e:
		frappe.throw(f"Error using canned response: {str(e)}")


@frappe.whitelist()
def get_canned_response_by_shortcut(shortcut):
	"""Get canned response by shortcut"""
	if not shortcut.startswith('/'):
		shortcut = '/' + shortcut

	shortcut = shortcut.strip().lower()

	canned_response = frappe.db.get_value(
		"HD Canned Response",
		{"shortcut": shortcut, "is_active": 1},
		["name", "title", "message"],
		as_dict=True
	)

	if canned_response:
		# Increment usage
		doc = frappe.get_doc("HD Canned Response", canned_response.name)
		doc.increment_usage()
		return canned_response

	return None
