# Copyright (c) 2021, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.website.website_generator import WebsiteGenerator
from frappe import _

class Article(WebsiteGenerator):
	def validate(self):
		category_doc = frappe.get_doc('Category', self.category)
		if category_doc.is_group:
			frappe.throw(_('Article category should not be a group'))

	def before_save(self):
		self.route = self.get_page_route()

	def get_page_route(self, route='', category=None):
		def change_case(str):
			res = [str[0].lower()]
			for c in str[1:]:
				if c in ('ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
					res.append('_')
					res.append(c.lower())
				elif c in (' '):
					continue
				else:
					res.append(c)
			
			return ''.join(res)

		if not category:
			category = self.category
		
		category_doc = frappe.get_doc('Category', category)
		route = f'{change_case(category_doc.name)}/{route}'
		
		if category_doc.parent_category:
			return self.get_page_route(route, category_doc.parent_category)
		else:
			return f'{route}{change_case(self.name)}'