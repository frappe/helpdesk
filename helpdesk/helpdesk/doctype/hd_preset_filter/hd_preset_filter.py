# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class HDPresetFilter(Document):
	def before_save(self):
		if self.type == "User":
			self.user = frappe.session.user

	def on_trash(self):
		if self.type == "System":
			frappe.throw("System filters cannot be deleted")

	def after_insert(self):
		frappe.publish_realtime("helpdesk:new-preset-filter", self)
