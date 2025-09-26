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
        self.validate_one_enabled_option()

    def validate_allowed_ratings(self):
        if self.rating not in self.allowed_ratings:
            frappe.throw(_("Rating {0} is not allowed").format(self.rating))

    def validate_bounds(self):
        if not (0.2 <= self.rating <= 1.0):
            frappe.throw(_("Rating must be between 0.2 and 1.0"))

    def validate_one_enabled_option(self):
        if not self.has_value_changed("disabled") and self.disabled == 1:
            return

        rating = self.rating
        count = frappe.db.count(
            "HD Ticket Feedback Option",
            filters={"rating": rating, "disabled": 0, "name": ["!=", self.name]},
        )
        if not count:
            frappe.throw(
                _("At least one feedback option must be enabled for rating {0}").format(
                    rating
                )
            )
