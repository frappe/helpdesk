# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.website.utils import cleanup_page_name


class HDTicketTemplate(Document):
	def validate(self):
		allowed_field_types = [
			"Link",
			"Select",
		]

		for field in self.fields:
			if field.fieldtype not in allowed_field_types:
				frappe.throw(
					f"Type {field.fieldtype} not allowed, should be in {allowed_field_types}"
				)
			if not field.fieldname:
				field.fieldname = cleanup_page_name(field.label)

			if field.fieldname == "description" and field.fieldtype != "Text Editor":
				frappe.throw("field type for description field should be Text Editor")

