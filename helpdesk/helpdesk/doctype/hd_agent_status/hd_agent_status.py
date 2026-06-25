# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from helpdesk.utils import publish_event


class HDAgentStatus(Document):
    def validate(self):
        self.validate_at_least_one_active()

    def on_update(self):
        if not self.enabled and self.has_value_changed("enabled"):
            self.reset_agents_when_disabled()

    def validate_at_least_one_active(self):
        """There must always be at least one enabled status in the Active category."""
        if self.category == "Active" and self.enabled:
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
                {"category": "Active", "enabled": 1, "name": ["!=", self.name]},
            )
        )

    def reset_agents_when_disabled(self):
        """Move agents holding a disabled status back to Active."""
        active_status = get_active_status()
        if not active_status:
            return

        agents = frappe.get_all(
            "HD Agent", filters={"availability": self.name}, pluck="name"
        )
        if not agents:
            return

        changed_on = frappe.utils.now()
        frappe.db.set_value(
            "HD Agent",
            {"name": ["in", agents]},
            {"availability": active_status, "availability_changed_on": changed_on},
        )
        publish_event(
            "agent_availability_updated",
            data={
                "agents": agents,
                "availability": active_status,
                "availability_changed_on": changed_on,
            },
        )


def get_active_status() -> str | None:
    """Name of an enabled status in the Active category (the default availability)."""
    return frappe.db.get_value(
        "HD Agent Status",
        {"category": "Active", "enabled": 1},
        "name",
        order_by="creation asc",
    )
