# Copyright (c) 2021, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.website.website_generator import WebsiteGenerator
from frappe.website.utils import cleanup_page_name


class Category(WebsiteGenerator):
	def before_save(self):
		self.route = self.get_page_route()

	def set_page_route(self):
		self.route = self.get_page_route()

	def get_page_route(self):
		return f"support/kb/{cleanup_page_name(self.name)}"