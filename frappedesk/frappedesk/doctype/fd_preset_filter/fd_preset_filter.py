# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class FDPresetFilter(Document):
	@staticmethod
	def get_assign_filter(assigned_to: str):
		return {
			"label": "Assigned To",
			"fieldname": "_assign",
			"filter_type": "is",
			"value": assigned_to,
		}

	@staticmethod
	def get_status_filter(status: str):
		return {
			"label": "Status",
			"fieldname": "status",
			"filter_type": "is",
			"value": status,
		}

	def before_save(self):
		if self.type == "User":
			self.user = frappe.session.user

	def on_trash(self):
		if self.type == "System":
			frappe.throw("System filters cannot be deleted")
