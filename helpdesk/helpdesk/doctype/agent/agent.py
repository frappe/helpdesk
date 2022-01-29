# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class Agent(Document):
	def before_save(self):
		user = frappe.get_doc("User", self.user)
		self.name = user.name
