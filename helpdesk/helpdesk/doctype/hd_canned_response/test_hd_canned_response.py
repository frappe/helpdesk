# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestHDCannedResponse(FrappeTestCase):
	def test_shortcut_validation(self):
		"""Test that shortcuts are automatically prefixed with /"""
		response = frappe.get_doc({
			"doctype": "HD Canned Response",
			"title": "Test Response",
			"shortcut": "test",
			"message": "This is a test response"
		})
		response.insert()

		self.assertEqual(response.shortcut, "/test")

		frappe.delete_doc("HD Canned Response", response.name)

	def test_usage_increment(self):
		"""Test usage count increments properly"""
		response = frappe.get_doc({
			"doctype": "HD Canned Response",
			"title": "Test Response 2",
			"message": "Test message"
		})
		response.insert()

		initial_count = response.usage_count
		response.increment_usage()
		response.reload()

		self.assertEqual(response.usage_count, initial_count + 1)
		self.assertIsNotNone(response.last_used)

		frappe.delete_doc("HD Canned Response", response.name)
