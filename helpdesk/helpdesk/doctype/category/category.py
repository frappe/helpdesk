# Copyright (c) 2021, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.utils.nestedset import NestedSet

class Category(NestedSet):
	def before_save(self):
		self.route = self.get_page_route()
		if self.linked_web_page:
			web_page = frappe.get_doc('Web Page', self.linked_web_page)
			self.sync_web_page_details(web_page)
			web_page.save()
		else:
			web_page = frappe.new_doc('Web Page')
			self.sync_web_page_details(web_page)
			web_page.insert()
			self.linked_web_page = web_page.name

	def sync_web_page_details(self, web_page):
		web_page.title = self.name
		web_page.route = self.route
		web_page.content_type = 'HTML'
		web_page.full_width = False
		
		import os
		with open(os.path.join(os.path.dirname(__file__), 'templates/category.html'), 'r') as web_template_file:
			web_page.main_section_html = web_template_file.read()
		
		categories = frappe.get_all('Category', fields=['name', 'description', 'thumbnail', 'parent_category', 'is_group'], filters={'parent_category': ['=', self.name]})
		web_page.context_script = f'context.categories = {categories}'
		
		web_page.published = True

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
			category = self.name
		
		category_doc = frappe.get_doc('Category', category)
		route = f'{change_case(category_doc.name)}{f"/{route}" if route else ""}'
		
		if category_doc.parent_category:
			return self.get_page_route(route, category_doc.parent_category)
		else:
			return f'hc/{route}'
