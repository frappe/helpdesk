# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class FDPresetFilter(Document):
	def validate(self):
		if self.type == "System":
			frappe.throw("Please set Type as Global or User instead of System")

	def on_trash(self):
		if self.type == "System":
			frappe.throw("System filters cannot be deleted")
