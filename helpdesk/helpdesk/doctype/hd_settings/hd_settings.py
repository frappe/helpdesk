# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from frappe.model.naming import append_number_if_name_exists
from frappe.model.document import Document
import frappe
from frappe.realtime import get_website_room
from helpdesk.utils import is_admin


class HDSettings(Document):
	def get_base_support_rotation(self):
		"""Returns the base support rotation rule if it exists, else creats once and returns it"""

		if not self.base_support_rotation:
			self.create_base_support_rotation()

		return self.base_support_rotation

	def create_base_support_rotation(self):
		"""Creates the base support rotation rule, and set it to frappe desk settings"""

		rule_doc = frappe.new_doc("Assignment Rule")
		rule_doc.name = append_number_if_name_exists(
			"Assignment Rule", "Support Rotation"
		)
		rule_doc.document_type = "HD Ticket"
		rule_doc.assign_condition = "status == 'Open'"
		rule_doc.priority = 0
		rule_doc.disabled = True  # Disable the rule by default, when agents are added to the group, the rule will be enabled

		for day in [
			"Monday",
			"Tuesday",
			"Wednesday",
			"Thursday",
			"Friday",
			"Saturday",
			"Sunday",
		]:
			day_doc = frappe.get_doc({"doctype": "Assignment Rule Day", "day": day})
			rule_doc.append("assignment_days", day_doc)

		rule_doc.save(ignore_permissions=True)
		self.base_support_rotation = rule_doc.name
		self.save(ignore_permissions=True)

		return

	def on_update(self):
		event = "helpdesk:settings-updated"
		room = get_website_room()

		frappe.publish_realtime(event, room=room, after_commit=True)
	

	def before_save(self):
		if self.time_entry_maxduration == '':
			self.time_entry_maxduration = None

		if self.time_entry_rounding == '':
			self.time_entry_rounding = None

		if self.paused_duration_threshold == '':
			self.paused_duration_threshold = None


@frappe.whitelist()
def get_timetracking_settings(customer=None):
	settings = frappe.get_single("HD Settings")
	enable_time_tracking = settings.enable_time_tracking
	max_duration = settings.time_entry_maxduration
	# Check if a customer is provided and if specific settings exist for this customer
	if customer:
		customer_settings = frappe.db.get_value("HD Customer", customer, "time_entry_maxduration")
		if customer_settings:
			max_duration = customer_settings  # Override max_duration with customer-specific settings

	enable_time_tracking = True if enable_time_tracking == 1 and not is_admin() else False
	max_duration = int(max_duration) * 1000 if max_duration else None  # Convert to milliseconds

	return {
		'enableTimeTracking': enable_time_tracking,
		'maxDuration': max_duration,
	}
