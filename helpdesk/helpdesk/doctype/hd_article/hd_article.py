# Copyright (c) 2021, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.query_builder import DocType
from frappe.utils import cint


class HDArticle(Document):
	@staticmethod
	def get_list_filters(query):
		QBArticle = DocType("HD Article")
		QBCategory = DocType("HD Article Category")

		query = (
			query.where(QBArticle.status != "Archived")
			.left_join(QBCategory)
			.on(QBCategory.name == QBArticle.category)
			.select(QBCategory.category_name)
			.select(
				QBArticle.title,
				QBArticle.status,
				QBArticle.views,
				QBArticle.author,
				QBArticle.modified,
			)
		)

		return query

	def before_insert(self):
		self.author = frappe.session.user

	def before_save(self):
		# set published date of the hd_article
		if self.status == "Published" and not self.published_on:
			self.published_on = frappe.utils.now()
		elif self.status == "Draft" and self.published_on:
			self.published_on = None

		if self.status == "Archived" and self.category != None:
			self.category = None

		# index is only set if its not set already, this allows defining index
		# at the time of creation itself if not set the index is set to the
		# last index + 1, i.e. the hd_article is added at the end
		if self.status == "Published" and self.idx == -1:
			self.idx = cint(
				frappe.db.count(
					"HD Article", {"category": self.category}, {"status": "Published"}
				)
			)

	@property
	def title_slug(self) -> str:
		"""
		Generate slug from article title.
		Example: "Introduction to Frappe Helpdesk" -> "introduction-to-frappe-helpdesk"

		:return: Generated slug
		"""
		return self.title.lower().replace(" ", "-")

	def get_breadcrumbs(self):
		breadcrumbs = [{"name": self.name, "label": self.title}]
		current_category = frappe.get_doc("Category", self.category)
		breadcrumbs.append(
			{"name": current_category.name, "label": current_category.category_name}
		)
		while current_category.parent_category:
			current_category = frappe.get_doc(
				"Category", current_category.parent_category
			)
			breadcrumbs.append(
				{"name": current_category.name, "label": current_category.category_name}
			)
		return breadcrumbs[::-1]


@frappe.whitelist(allow_guest=True)
def add_feedback(hd_article, helpful):
	# TODO: use a base 5 or 10 rating system instead of a boolean
	field = "helpful" if helpful else "not_helpful"

	value = cint(frappe.db.get_value("HD Article", hd_article, field))
	frappe.db.set_value(
		"HD Article", hd_article, field, value + 1, update_modified=False
	)


@frappe.whitelist(allow_guest=True)
def increment_view(hd_article):
	value = cint(frappe.db.get_value("HD Article", hd_article, "views"))
	frappe.db.set_value(
		"HD Article", hd_article, "views", value + 1, update_modified=False
	)
