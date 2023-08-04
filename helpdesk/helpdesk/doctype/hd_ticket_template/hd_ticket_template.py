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
			custom_field_exists = frappe.db.exists(
				{"doctype": "Custom Field", "fieldname": f.fieldname, "dt": "HD Ticket"}
			)
			if not custom_field_exists:
				text = _("Custom Field `{0}` does not exist in Ticket").format(
					f.fieldname
				)
				frappe.throw(text, frappe.DoesNotExistError)

	def prevent_default_delete(self):
		if self.name == DEFAULT_TICKET_TEMPLATE:
			text = _("Default template can not be deleted")
			frappe.throw(text, frappe.PermissionError)
