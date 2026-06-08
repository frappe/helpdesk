# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class HDFacility(Document):
	def validate(self):
		# Validate that subcounty belongs to selected county
		if self.county and self.subcounty:
			subcounty_county = frappe.db.get_value('HD Subcounty', self.subcounty, 'county')
			if subcounty_county != self.county:
				frappe.throw(f"Subcounty '{self.subcounty}' does not belong to county '{self.county}'")

	def before_save(self):
		# Format phone numbers
		if self.phone_number:
			self.phone_number = self.format_phone_number(self.phone_number)
		if self.alternative_phone:
			self.alternative_phone = self.format_phone_number(self.alternative_phone)

	def format_phone_number(self, phone):
		# Remove spaces and special characters
		phone = ''.join(filter(str.isdigit, phone))

		# Kenya phone number formatting
		if phone.startswith('0') and len(phone) == 10:
			# Convert 0XXX to +254XXX
			return f"+254{phone[1:]}"
		elif phone.startswith('254') and len(phone) == 12:
			return f"+{phone}"
		elif phone.startswith('+254'):
			return phone

		return phone
