# Copyright (c) 2021, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import cint


class Article(Document):
	def before_insert(self):
		self.author = frappe.session.user

	def before_save(self):
		# set published date of the article
		if self.status == "Published" and not self.published_on:
			self.published_on = frappe.utils.now()
		else:
			self.published_on = None

		# index is only set if its not set already, this allows defining index at the time of creation itself
		# if not set the index is set to the last index + 1, i.e. the article is added at the end
		if self.status == "Published" and self.idx == -1:
			self.idx = cint(frappe.db.count("Article", {"category": self.category}, {"status": "Published"}))

@frappe.whitelist(allow_guest=True)
def add_feedback(article, helpful):
	# TODO: use a base 5 or 10 rating system instead of a boolean
	field = "helpful" if helpful else "not_helpful"

	value = cint(frappe.db.get_value("Article", article, field))
	frappe.db.set_value("Article", article, field, value + 1, update_modified=False)


@frappe.whitelist(allow_guest=True)
def increment_view(article):
	value = cint(frappe.db.get_value("Article", article, "views"))
	frappe.db.set_value("Article", article, "views", value + 1, update_modified=False)
