# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class HDTicketTemplate(Document):
	def validate(self):
		self.verify_field_exists()

	def verify_field_exists(self):
		for f in self.fields:
			docfield_exits = frappe.db.exists(
				{"doctype": "DocField", "fieldname": f.fieldname, "parent": "HD Ticket"}
			)
			custom_field_exists = frappe.db.exists(
				{"doctype": "Custom Field", "fieldname": f.fieldname, "dt": "HD Ticket"}
			)
			if not docfield_exits and not custom_field_exists:
				text = _("Field `{0}` does not exist in Ticket").format(f.fieldname)
				frappe.throw(text, frappe.DoesNotExistError)
