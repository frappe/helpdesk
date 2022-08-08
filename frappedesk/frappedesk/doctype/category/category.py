# Copyright (c) 2021, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.website.website_generator import WebsiteGenerator
from frappe.website.utils import cleanup_page_name


class Category(WebsiteGenerator):
	def validate(self):
		self.validate_tree()

	def validate_tree(self):
		if self.is_group:
			if self.parent_category:
				frappe.throw(_("Can only create category with atmost a single nesting"))

	def before_insert(self):
		if self.is_group:
			all_group_categories = frappe.get_all("Category", filters={"is_group": ["=", "1"]}, pluck="name")
			if(len(all_group_categories) >= 6):
				frappe.throw(_("Can only create a maximum of 6 groups categories"))

	#TODO: when renamed, website route should be updated
	def before_save(self):
		if self.is_group or self.parent_category:
			self.route = self.get_page_route()

	def set_page_route(self):
		self.route = self.get_page_route()

	def get_page_route(self, route="", category=None):
		if not category:
			category = self.name
			category_doc = self
		else:
			category_doc = frappe.get_doc("Category", category)

		scrubbed_title = cleanup_page_name(category_doc.category_name)
		route = f'{scrubbed_title}{f"/{route}" if route else ""}'

		if category_doc.parent_category:
			return self.get_page_route(route, category_doc.parent_category)
		else:
			return f"support/kb/{route}"
