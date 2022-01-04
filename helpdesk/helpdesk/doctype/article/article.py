# Copyright (c) 2021, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _, throw

class Article(Document):
	def validate(self):
		category_doc = frappe.get_doc('Category', self.category)
		if category_doc.is_group:
			frappe.throw(_('Article category should not be a group'))

	def before_insert(self):
		web_page = frappe.new_doc('Web Page')
		self.sync_web_page_details(web_page)
		web_page.insert()
		
		self.linked_web_page = web_page.name

	def before_save(self):
		if self.linked_web_page:	
			web_page = frappe.get_doc('Web Page', self.linked_web_page)
			self.sync_web_page_details(web_page)
			web_page.save()
		else:
			throw(_('Web page was not created on insert, need to handle this case'))

	def sync_web_page_details(self, web_page):
			web_page.title = self.title
			web_page.content_type = 'HTML'
			web_page.main_section_html = self.content
			web_page.published = self.published
			web_page.show_title = True
			# TODO: create dynamic route with help of category
			web_page.route = 'temp_category/temp_article'