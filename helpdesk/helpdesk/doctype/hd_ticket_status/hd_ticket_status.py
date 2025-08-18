# Copyright (c) 2025, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class HDTicketStatus(Document):
    def validate(self):
        self.validate_closed_status_change()
        self.validate_required_categories()
        self.validate_default_status()

    def validate_closed_status_change(self):
        if self.is_new():
            return
        old_name = (
            self.get_doc_before_save().name if self.get_doc_before_save() else None
        )
        if old_name == "Closed" and not self.has_value_changed("order"):
            # Prevent modification or deletion of the 'Closed' status
            frappe.throw(_("The 'Closed' status cannot be modified or deleted."))

    def validate_required_categories(self):
        if self.is_new():
            return
        if not self.has_value_changed("category"):
            return
        old_category = (
            self.get_doc_before_save().category if self.get_doc_before_save() else None
        )

        if not old_category:
            return

        # If category is being changed, check if we're removing the last status of a required category
        if old_category != self.category:
            count = frappe.db.count(
                "HD Ticket Status",
                {"category": old_category, "name": ["!=", self.name]},
            )

            if count == 0:
                frappe.throw(
                    _(
                        f"At least one ticket status with category '{old_category}' must exist in the system."
                    )
                )

    def validate_default_status(self):
        if not self.has_value_changed("default_status"):
            return
        if self.category != "Open":
            return

        if self.default_status:
            existing_fallback = frappe.db.exists(
                "HD Ticket Status",
                {"category": "Open", "default_status": 1, "name": ["!=", self.name]},
            )
            if existing_fallback:
                frappe.db.set_value(
                    "HD Ticket Status", existing_fallback, "default_status", 0
                )
        else:
            count = frappe.db.count(
                "HD Ticket Status",
                {"category": "Open", "default_status": 1, "name": ["!=", self.name]},
            )
            if count == 0:
                frappe.throw(
                    _(
                        "At least one fallback status must be set for the 'Open' category."
                    )
                )

    def before_save(self):
        self.update_customer_label()

    def update_customer_label(self):
        if self.different_view:
            return
        self.label_customer = self.label_agent
