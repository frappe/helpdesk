# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class HDAgentStatus(Document):
    def validate(self):
        self.validate_at_least_one_active()

    def validate_at_least_one_active(self):
        """There must always be at least one enabled status in the Active category."""
        if self.category == "Active" and self.enable:
            return  # this status keeps an enabled Active status around

        if self.is_new():
            return  # a new status cannot remove an existing one

        if self.has_other_enabled_active():
            return

        frappe.throw(_("At least one enabled Active status is required."))

    def on_trash(self):
        if self.category == "Active" and not self.has_other_enabled_active():
            frappe.throw(_("At least one enabled Active status is required."))

    def has_other_enabled_active(self) -> bool:
        return bool(
            frappe.db.exists(
                "HD Agent Status",
                {"category": "Active", "enable": 1, "name": ["!=", self.name]},
            )
        )


def get_active_status() -> str | None:
    """Name of an enabled status in the Active category (the default availability)."""
    return frappe.db.get_value(
        "HD Agent Status", {"category": "Active", "enable": 1}, "name"
    )
