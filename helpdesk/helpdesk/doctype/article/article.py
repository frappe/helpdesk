# Copyright (c) 2021, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _

class Article(Document):
	def validate(self):
		category_doc = frappe.get_doc('Category', self.category)
		if category_doc.is_group:
			frappe.throw(_('Article category should not be a group'))
