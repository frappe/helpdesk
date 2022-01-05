# Copyright (c) 2021, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.website.website_generator import WebsiteGenerator
from frappe import _
from frappe.utils import cint

class Article(WebsiteGenerator):
	def validate(self):
		category_doc = frappe.get_doc('Category', self.category)
		if category_doc.is_group:
			frappe.throw(_('Article category should not be a group'))

	def before_save(self):
		self.route = self.get_page_route()

	def get_page_route(self):
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

		category_doc = frappe.get_doc('Category', self.category)
		return f'{category_doc.route}{change_case(self.name)}'

@frappe.whitelist(allow_guest=True)
def add_feedback(article, helpful):
	field = "helpful"
	if helpful == "No":
		field = "not_helpful"

	value = cint(frappe.db.get_value("Article", article, field))
	frappe.db.set_value("Article", article, field, value+1, update_modified=False)

@frappe.whitelist(allow_guest=True)
def increment_view(article):	
	value = cint(frappe.db.get_value("Article", article, 'views'))
	frappe.db.set_value("Article", article, 'views', value+1, update_modified=False)
