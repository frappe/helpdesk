# Copyright (c) 2023, Frappe Technologies and contributors
# For license information, please see license.txt

import re

import frappe
from frappe import _
from frappe.model.document import Document

HAS_RES_REGEX = "res\s?=\s?.+"


class HDDashboardItem(Document):
	def before_save(self):
		if not re.search(HAS_RES_REGEX, self.snippet):
			frappe.throw(
				_("Snippet must assign the `res` variable!"),
				title=_("Invalid Snippet"),
			)
