# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


class TicketCustomFieldsConfig(Document):
	def get_field_info(self, fieldname):
		custom_field_item = next(
			(
				field
				for field in self.custom_fields
				if field.custom_field.split("-")[1] == fieldname
			),
			None,
		)
		if custom_field_item:
			return custom_field_item.as_dict()
		else:
			return {}

	def get_custom_fields(self, view=None):
		def filter(field, view):
			if view == "Agent Portal":
				return field.show_in_agent_portal
			elif view == "Customer Portal":
				return field.show_in_customer_portal
			return True

		def get_dict(field, view):
			dict = {"fieldname": frappe.get_doc("Custom Field", field.custom_field).fieldname}
			if view == "Agent Portal":
				dict.update(
					{
						"show_in_agent_portal": field.show_in_agent_portal,
						"is_editable_by_agent": field.is_editable_by_agent,
					}
				)
			elif view == "Customer Portal":
				dict.update(
					{
						"show_in_customer_portal": field.show_in_customer_portal,
						"is_editable_by_customer": field.is_editable_by_customer,
					}
				)
			return dict

		return [get_dict(field, view) for field in self.custom_fields if filter(field, view)]
