# Copyright (c) 2021, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.website.website_generator import WebsiteGenerator


class Category(WebsiteGenerator):
	def validate(self):
		self.validate_tree()

	def validate_tree(self):
		if self.parent_category:
			parent_category_doc = frappe.get_doc("Category", self.parent_category)
			if not parent_category_doc.is_group:
				frappe.throw(_("Parent category should be a group category"))
		# Limit the tree depth to 2
		if self.is_group:
			if self.parent_category:
				frappe.throw(_("Can only create category with atmost a single nesting"))
		else:
			if not self.parent_category:
				frappe.throw(_("Can only create leaf nodes within a parent category"))

	def before_save(self):
		self.route = self.get_page_route()

	def get_page_route(self, route="", category=None):
		def change_case(str):
			res = [str[0].lower()]
			for c in str[1:]:
				if c in ("ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"):
					res.append("_")
					res.append(c.lower())
				elif c in (" "):
					continue
				else:
					res.append(c)

			return "".join(res)

		if not category:
			category = self.name
			category_doc = self
		else:
			category_doc = frappe.get_doc("Category", category)

		route = f'{change_case(category_doc.category_name)}{f"/{route}" if route else ""}'

		if category_doc.parent_category:
			return self.get_page_route(route, category_doc.parent_category)
		else:
			return f"support/kb/{route}"
