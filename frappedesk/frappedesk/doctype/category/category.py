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
		
	def after_insert(self):
		self.update_article_and_sub_category_ordering()

	#TODO: when renamed, website route should be updated
	def before_save(self):
		if self.is_group or self.parent_category:
			self.route = self.get_page_route()

	def on_update(self):
		self.update_article_and_sub_category_ordering()

	def update_article_and_sub_category_ordering(self):
		if self.is_group:
			# reset previous sub categories to null
			all_previous_sub_categories = frappe.get_all("Category", filters={"parent_category": ["=", self.name]}, pluck="name")
			for category in all_previous_sub_categories:
				category_doc = frappe.get_doc("Category", category)
				category_doc.parent_category = ""
				category_doc.order = None
				category_doc.save()

			# set parent_category fields for all the sub_cateogries
			for index, category in enumerate(self.sub_categories):
				category_doc = frappe.get_doc("Category", category.sub_category)
				if category_doc:
					if not category_doc.is_group:
						if not category_doc.parent_category or category_doc.parent_category == self.name:
							category_doc.parent_category = self.name
							category_doc.order = index
							category_doc.set_page_route()
							category_doc.save()
						else:
							frappe.throw(_(f"{category_doc.category_name} is already a child category of {category_doc.parent_category}, please remove it and try again"))
					else:
						frappe.throw(_(f"{category_doc.category_name} is a group category, and cannot be added as a sub category"))
				else:
					frappe.throw(_(f"No category named {category.sub_category} found"))
		else:
			# reset previous article with this category to null
			all_previous_category_articles = frappe.get_all("Article", filters={"category": ["=", self.name]})
			for article in all_previous_category_articles:
				article_doc = frappe.get_doc("Article", article)
				article_doc.category = ""
				article_doc.order = None
				article_doc.save()
			
			# set parent_category fields for all the sub_cateogries
			for index, article in enumerate(self.articles):
				article_doc = frappe.get_doc("Article", article.article)
				if article_doc:
					if not article_doc.category or article_doc.category == self.name:
						article_doc.category = self.name
						article_doc.order = index
						article_doc.set_page_route()
						article_doc.save()
					else:
						frappe.throw(_(f"{article_doc.title} is already a child category of {article_doc.category}, please remove it and try again"))
				else:
					frappe.throw(_(f"No article named {article.article} found"))

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
