# Copyright (c) 2021, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint
from frappe.model.naming import append_number_if_name_exists
import json


class Category(Document):
	def before_save(self):
		if self.idx == -1 and self.status == "Published":
			# index is only set if its not set already, this allows defining index at the time of creation itself
			# if not set the index is set to the last index + 1, i.e. the category is added at the end
			self.idx = cint(
				frappe.db.count("Category", {"parent_category": self.parent_category})
			)

	def archive(self):
		self.idx = -1
		self.status = "Archived"
		self.save()
		self.rename(append_number_if_name_exists("Category", self.name + ".archived"))

	def unarchive(self):
		self.status = "Published"
		self.rename(self.name.replace(".archived", ""))
		self.save()

	def get_breadcrumbs(self):
		breadcrumbs = [{"name": self.name, "label": self.category_name}]
		current_category = self
		while current_category.parent_category:
			current_category = frappe.get_doc("Category", current_category.parent_category)
			breadcrumbs.append(
				{"name": current_category.name, "label": current_category.category_name}
			)
		return breadcrumbs[::-1]
