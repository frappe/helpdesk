# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


class TicketCustomFieldsConfig(Document):
	def get_field_info(self, fieldname):
		custom_field_item = next(
			(field for field in self.custom_fields if field.fieldname == fieldname), None
		)
		if custom_field_item:
			return custom_field_item.as_dict()
		else:
			return {}
