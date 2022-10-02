# Copyright (c) 2021, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint
from frappe.model.naming import append_number_if_name_exists


class Category(Document):
	def before_save(self):
		if self.is_group and self.parent_category:
			# max 2 levels
			# eg: Category 1 
			#		+---> Category 2
			#		|		+---> Article 1			(allowed)
			# 		+---> Article 2 				(allowed)
			# 		+---> Category 3
			# 				+---> Category 4  		(not allowed)
			frappe.throw(_("Group Category cannot have a parent category"))
		if self.idx == -1 and self.status == "Published":
			# index is only set if its not set already, this allows defining index at the time of creation itself
			# if not set the index is set to the last index + 1, i.e. the category is added at the end
			self.idx = cint(frappe.db.count("Category", {"parent_category": self.parent_category}))

	def archive(self):
		self.idx = -1
		self.status = "Archived"
		self.rename(append_number_if_name_exists("Category", self.name + ".archived"))
		self.save()

	def unarchive(self):
		self.status = "Published"
		self.rename(self.name.replace(".archived", ""))
		self.save()