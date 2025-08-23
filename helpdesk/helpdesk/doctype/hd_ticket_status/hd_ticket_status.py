# Copyright (c) 2025, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class HDTicketStatus(Document):
    def validate(self):
        self.validate_closed_status_change()
        self.validate_required_categories()

    def validate_closed_status_change(self):
        if self.is_new():
            return
        old_name = (
            self.get_doc_before_save().name if self.get_doc_before_save() else None
        )
        if old_name == "Closed" and not (
            self.has_value_changed("order") or self.has_value_changed("color")
        ):
            frappe.throw(
                _(
                    "Only the 'color' and 'order' fields of the 'Closed' status can be modified."
                )
            )

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

    # TODO: if category is changed check if linked to HD Settings or HD SLA with reopen or default status
    # if so throw error saying to change those first
