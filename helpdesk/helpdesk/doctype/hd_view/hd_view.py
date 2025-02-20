# Copyright (c) 2025, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class HDView(Document):
    def validate(self):
        self.validate_default_view()

    def validate_default_view(self):
        if not self.is_default:
            return

        default_view_exists = frappe.db.exists(
            "HD View",
            {
                "is_default": 1,
                "name": ("!=", self.name),
                "user": frappe.session.user,
                "dt": self.dt,
            },
        )

        if default_view_exists:
            frappe.throw(
                _("Only one default view is allowed per user for {0}").format(self.dt)
            )

    def before_save(self):
        self.toggle_pinned_public_view()

    def toggle_pinned_public_view(self):
        if self.pinned and self.public:
            if self.has_value_changed("pinned"):
                self.public = 0
            if self.has_value_changed("public"):
                self.pinned = 0
