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
        if self.enabled:
            return

        self.reject_if_default()

    def reject_if_default(self):
        """The status HD Settings points at has to stay available: it is where
        new agents start and where agents land when their status is retired.

        Reads the setting directly rather than through get_default_agent_status:
        if no default is named, there is nothing to protect, not an error.
        """
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
        """Move agents off a status the admin just retired.

        Left alone they keep a status that is no longer offered: it is filtered
        out of the picker, so their own menu renders empty while everyone else
        still sees the retired status against their name.

        TODO: notify each agent that their status was reset. HD Notification is
        ticket-shaped today (notification_type is a Select of
        Assignment/Mention/Reaction and user_from is mandatory), so this waits
        on the notification refactor; the socket toast covers it meanwhile.
        """
        if self.enabled or not self.has_value_changed("enabled"):
            return

        default_status = get_default_agent_status()
        # One save at a time so HD Agent's controller does the validation, the
        # availability_changed_on stamp and the realtime broadcast. save() also
        # re-reads under a lock, so an agent who moved themselves meanwhile wins.
        # ponytail: synchronous. Enqueue if one status ever holds enough agents
        # for the request to time out.
        for name in frappe.get_all(
            "HD Agent", filters={"availability": self.name}, pluck="name"
        ):
            agent = frappe.get_doc("HD Agent", name)
            agent.availability = default_status
            agent.save(ignore_permissions=True)


def get_default_agent_status() -> str:
    """The status new agents start on, and where agents land when the status
    they are on is retired.

    Named in HD Settings rather than inferred from an ordering: with more than
    one enabled status any ordering picks a winner silently, and this now moves
    existing agents in bulk.
    """
    status = frappe.db.get_single_value("HD Settings", "default_agent_status")
    if not status:
        frappe.throw(_("Set a default agent status in HD Settings."))

    return status
