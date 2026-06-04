# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class HDAgentStatus(Document):
    def validate(self):
        self.validate_single_active_category()
        self.validate_active_status_protected()

    def validate_single_active_category(self):
        """Only one status may belong to the Active category."""
        if self.category != "Active":
            return

        existing = frappe.db.get_value(
            "HD Agent Status",
            {"category": "Active", "name": ["!=", self.name]},
            "name",
        )
        if existing:
            frappe.throw(
                _(
                    "Only one Active status is allowed. {0} already uses the Active category."
                ).format(existing),
                title=_("Active Status Already Exists"),
            )

    def validate_active_status_protected(self):
        """The Active status must always stay enabled and in the Active category."""
        if self.category == "Active" and not self.enable:
            frappe.throw(_("The Active status must stay enabled."))

        if self.is_new():
            return

        was_active = (
            frappe.db.get_value("HD Agent Status", self.name, "category") == "Active"
        )
        if was_active and self.category != "Active":
            frappe.throw(_("The Active status cannot be moved to another category."))

    def on_trash(self):
        if self.category == "Active":
            frappe.throw(_("The Active status cannot be deleted."))


def get_active_status() -> str | None:
    """Name of the (single) status in the Active category."""
    return frappe.db.get_value("HD Agent Status", {"category": "Active"}, "name")
