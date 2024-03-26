# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class HDCustomer(Document):
	
	def before_save(self):
		if self.time_entry_maxduration == '':
			self.time_entry_maxduration = None

		if self.time_entry_rounding == '':
			self.time_entry_rounding = None

