# Copyright (c) 2023, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class HDTicketFeedbackOption(Document):
	allowed_ratings = [0.2, 0.4, 0.6, 0.8, 1.0]

	def validate(self):
		self.validate_allowed_ratings()
		self.validate_bounds()

	def validate_allowed_ratings(self):
		if self.rating not in self.allowed_ratings:
			frappe.throw(_("Rating {0} is not allowed").format(self.rating))

	def validate_bounds(self):
		if not (0.2 <= self.rating <= 1.0):
			frappe.throw(_("Rating must be between 0.2 and 1.0"))
