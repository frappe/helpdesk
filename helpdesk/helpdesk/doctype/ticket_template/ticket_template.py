# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.website.utils import cleanup_page_name

class TicketTemplate(Document):
	def validate(self):
		allowed_field_types = ['Data', 'Link', 'Long Text', 'Text Editor']

		for field in self.fields:
			if field.fieldtype not in allowed_field_types:
				frappe.throw(f'Type {field.fieldtype} not allowed, should be in {allowed_field_types}')
			if not field.fieldname:
				field.fieldname = cleanup_page_name(field.label)

		required_fields_not_added = []
		for fieldname in ['subject', 'description']:
			if not next((field for field in self.fields if field.fieldname == fieldname), None):
				required_fields_not_added.append(fieldname)

		if len(required_fields_not_added) > 0:
			frappe.throw(f'template mandetory fields {required_fields_not_added} are not added')


	def before_save(self):
		self.template_route = cleanup_page_name(self.template_name)