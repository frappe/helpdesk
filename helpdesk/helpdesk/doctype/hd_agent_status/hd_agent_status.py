# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class HDAgentStatus(Document):
    def validate(self):
        self.validate_at_least_one_active()

    def on_update(self):
        if not self.enabled and self.has_value_changed("enabled"):
            self.reset_agents_to_active()

    def reset_agents_to_active(self):
        """Move agents off a status the admin just retired.

        Left alone they keep a status that is no longer offered: it is filtered
        out of the picker, so their own menu renders empty while everyone else
        still sees the retired status against their name.

        Saved one at a time rather than bulk-updated so HD Agent's controller
        does the validation, the availability_changed_on stamp and the realtime
        broadcast — the same path every other availability change takes.

        TODO: notify each agent that their status was reset because it was
        disabled. HD Notification is ticket-shaped today (notification_type is a
        Select of Assignment/Mention/Reaction and user_from is mandatory), so
        this waits on the notification refactor; the socket toast covers it
        meanwhile.
        """
        active_status = get_active_status()
        if not active_status:
            return

        for name in frappe.get_all(
            "HD Agent", filters={"availability": self.name}, pluck="name"
        ):
            agent = frappe.get_doc("HD Agent", name)
            agent.availability = active_status
            agent.save(ignore_permissions=True)

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


def get_active_status() -> str | None:
    """Name of an enabled status in the Active category (the default availability).

    With more than one enabled Active status the oldest wins: frappe.db.get_value
    resolves its default order_by to `creation`. Deliberately not `status_order` —
    the shipped statuses are 10/20/30 and a new one defaults to 0, so ordering by
    it would silently promote any custom status above "Active".
    """
    return frappe.db.get_value(
        "HD Agent Status", {"category": "Active", "enabled": 1}, "name"
    )
