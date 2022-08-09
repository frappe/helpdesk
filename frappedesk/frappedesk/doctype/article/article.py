# Copyright (c) 2021, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.website.website_generator import WebsiteGenerator
from frappe import _
from frappe.utils import cint
from frappe.website.utils import (cleanup_page_name, get_html_content_based_on_type)

class Article(WebsiteGenerator):
	def before_insert(self):
		self.author = frappe.session.user

	#TODO: when renamed, website route should be updated
	def before_save(self):
		if self.category:
			self.route = self.get_page_route()

		if not self.published:
			self.published_on = None
		if not self.published_on and self.published:
			self.published_on = frappe.utils.now()

	def set_page_route(self):
		self.route = self.get_page_route()

	def get_page_route(self):
		category_doc = frappe.get_doc("Category", self.category)
		scrubbed_title = cleanup_page_name(self.title)
		return f"{category_doc.route}/{scrubbed_title}"

	def get_context(self, context):
		context.content = get_html_content_based_on_type(self, 'content', self.content_type)

		return context

@frappe.whitelist(allow_guest=True)
def add_feedback(article, helpful):
	field = "helpful"
	if helpful == "No":
		field = "not_helpful"

	value = cint(frappe.db.get_value("Article", article, field))
	frappe.db.set_value("Article", article, field, value + 1, update_modified=False)


@frappe.whitelist(allow_guest=True)
def increment_view(article):
	value = cint(frappe.db.get_value("Article", article, "views"))
	frappe.db.set_value("Article", article, "views", value + 1, update_modified=False)
