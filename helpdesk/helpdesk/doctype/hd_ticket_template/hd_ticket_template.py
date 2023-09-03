# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from helpdesk.consts import DEFAULT_TICKET_TEMPLATE


class HDTicketTemplate(Document):
	def validate(self):
		self.verify_field_exists()

	def on_trash(self):
		self.prevent_default_delete()

	def verify_field_exists(self):
		for f in self.fields:
			exists = self.docfield_exists(f.fieldname) or self.custom_field_exists(
				f.fieldname
			)
			if not exists:
				text = _("Field `{0}` does not exist in Ticket").format(f.fieldname)
				frappe.throw(text)

	def docfield_exists(self, fieldname: str):
		return frappe.db.exists(
			{
				"doctype": "DocField",
				"fieldname": fieldname,
				"parent": "HD Ticket",
			}
		)

	def custom_field_exists(self, fieldname: str):
		return frappe.db.exists(
			{
				"doctype": "Custom Field",
				"fieldname": fieldname,
				"dt": "HD Ticket",
			}
		)

	def prevent_default_delete(self):
		if self.name == DEFAULT_TICKET_TEMPLATE:
			text = _("Default template can not be deleted")
			frappe.throw(text, frappe.PermissionError)
