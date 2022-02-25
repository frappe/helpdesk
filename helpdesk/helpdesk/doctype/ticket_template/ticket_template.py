# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class TicketTemplate(Document):
	def validate(self):
		allowed_field_types = ['Data', 'Link']

		for field in self.fields:
			if field.fieldtype not in allowed_field_types:
				frappe.throw(f'Type {field.fieldtype} not allowed, should be in {allowed_field_types}')

