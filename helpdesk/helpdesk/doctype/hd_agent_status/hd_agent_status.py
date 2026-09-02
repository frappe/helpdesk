# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class HDAgentStatus(Document):
    def validate(self):
        self.validate_default_stays_enabled()

    def on_update(self):
        self.reset_agents_to_default()

    def on_trash(self):
        self.reject_if_default()

    def validate_default_stays_enabled(self):
        # check only when disabling, already disabled statuses should still
        # save fine
        if self.enabled or not self.has_value_changed("enabled"):
            return

        self.reject_if_default()

    def reject_if_default(self):
        """Block disabling or deleting the default status, agents get created
        on it and moved to it."""
        if self.name != frappe.db.get_single_value(
            "HD Settings", "default_agent_status"
        ):
            return

        frappe.throw(
            _(
                "{0} is the default agent status. Set a different default in HD Settings first."
            ).format(self.name)
        )

    def reset_agents_to_default(self):
        """Move agents off a disabled status, else they get stuck on a status
        the picker no longer shows.

        TODO: send an in-app notification too, HD Notification only supports
        ticket notifications right now. The toast covers it for now.
        """
        if self.enabled or not self.has_value_changed("enabled"):
            return

        # on_update fires on insert too, a new status has no agents anyway
        agents = frappe.get_all(
            "HD Agent", filters={"availability": self.name}, pluck="name"
        )
        if not agents:
            return

        default_status = get_default_agent_status()
        # save via the controller so validation, timestamp and realtime
        # updates all happen. save() also catches an agent changing their
        # status at the same time
        for name in agents:
            agent = frappe.get_doc("HD Agent", name)
            agent.availability = default_status
            agent.save(ignore_permissions=True)


def get_default_agent_status() -> str:
    """Default status from HD Settings, new agents start on it and agents
    get moved to it when their status is disabled."""
    status = frappe.db.get_single_value("HD Settings", "default_agent_status")
    if not status:
        frappe.throw(_("Set a default agent status in HD Settings."))

    return status
