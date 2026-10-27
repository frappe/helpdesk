# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime, now_datetime

from helpdesk.helpdesk.doctype.hd_agent_status.hd_agent_status import (
    get_default_agent_status,
)
from helpdesk.utils import capture_event, is_agent_manager, publish_event


class HDAgent(Document):
    def before_insert(self):
        if not self.availability:
            self.availability = get_default_agent_status()

    def validate(self):
        self.validate_availability()
        self.validate_availability_expiry()

    def before_save(self):
        old_doc = self.get_doc_before_save()
        if self.has_value_changed("availability"):
            self.availability_changed_on = frappe.utils.now()
            self.availability_changed_by = self.get_availability_changed_by()
        if old_doc and old_doc.agent_name != self.agent_name:
            if self.agent_name:
                agent_name = self.agent_name.split()
                frappe.set_value(
                    "User",
                    self.user,
                    {
                        "first_name": agent_name[0],
                        "last_name": " ".join(agent_name[1:]),
                    },
                )
            else:
                self.agent_name = frappe.get_value("User", self.user, "full_name")

        if old_doc and old_doc.user_image != self.user_image:
            frappe.set_value("User", self.user, "user_image", self.user_image)

        if self.name == self.user:
            return

        self.name = self.user
        self.set_user_roles()

    def on_update(self):
        self.publish_availability_update()
        self.capture_availability_telemetry()

    def validate_availability(self):
        """Only an enabled HD Agent Status may be set as availability.

        Guarded on the value actually changing so an agent whose status was
        disabled after the fact can still save unrelated fields.
        """
        if not self.availability or not self.has_value_changed("availability"):
            return

        if not frappe.db.exists(
            "HD Agent Status", {"name": self.availability, "enabled": 1}
        ):
            frappe.throw(_("Invalid availability"), frappe.ValidationError)

    def validate_availability_expiry(self):
        if not self.availability_expires_on:
            return

        # a new status starts without a timer, and the default status has
        # nothing to reset to
        expiry_changed = self.has_value_changed("availability_expires_on")
        if (
            self.has_value_changed("availability") and not expiry_changed
        ) or self.availability == get_default_agent_status():
            self.availability_expires_on = None
            return

        if expiry_changed and self.availability_expired():
            frappe.throw(_("Pick a time in the future."))

    def reset_availability(self):
        """Move the agent to the default status. Saves through the controller
        so the timestamp and the realtime update happen as for any change."""
        self.availability = get_default_agent_status()
        self.save(ignore_permissions=True)

    def expire_availability(self):
        """Reset a status whose timer ran out. Credited to the agent, who set
        the timer, so it does not read as someone else changing it."""
        # the agent may have changed status since the scheduler queried
        if not self.availability_expired():
            return
        self.flags.availability_changed_by = self.user
        self.reset_availability()

    def availability_expired(self) -> bool:
        return (
            bool(self.availability_expires_on)
            and get_datetime(self.availability_expires_on) <= now_datetime()
        )

    def get_availability_changed_by(self) -> str:
        return self.flags.get("availability_changed_by") or frappe.session.user

    def availability_changed(self) -> bool:
        """Whether this save changes the availability of an existing agent.

        Inserts are excluded: has_value_changed is True when there is no doc
        before save, but a new agent seeded with a default has not changed
        anything. Note validate_availability deliberately does not use this —
        a new agent must still be validated.
        """
        return bool(self.get_doc_before_save()) and self.has_value_changed(
            "availability"
        )

    def publish_availability_update(self):
        """Broadcast an availability change to every connected client."""
        # an expiry-only change still has to reach the agent's other tabs
        if not (
            self.availability_changed()
            or self.has_value_changed("availability_expires_on")
        ):
            return

        publish_event(
            "agent_availability_updated",
            data={
                "agent": self.name,
                "availability": self.availability,
                "availability_changed_on": self.availability_changed_on,
                "availability_expires_on": self.availability_expires_on,
                # so the client can tell if someone else changed their status
                "changed_by": self.get_availability_changed_by(),
            },
        )

    def capture_availability_telemetry(self):
        if not self.availability_changed():
            return

        capture_event("agent_availability_updated")

    def set_user_roles(self):
        user = frappe.get_doc("User", self.user)
        for role in ["Agent"]:
            user.append("roles", {"role": role})
        user.save(ignore_permissions=True)


def has_permission(doc: Document, ptype: str, user: str) -> bool:
    """Per-record access for HD Agent.

    An agent may only modify their own record — the Agent role grants blanket
    write on the doctype, which is what let one agent edit another's. Reads stay
    open so presence dots and assignment pickers can still list every agent, and
    managers are unrestricted.
    """
    if ptype not in ("write", "delete"):
        return True

    return is_agent_manager(user) or doc.user == user


def reset_expired_availability():
    """Scheduler job: move agents whose status timer ran out to the default."""
    # cutoff from python, sql NOW() is wrong when the db timezone differs
    # from the system timezone
    agents = frappe.get_all(
        "HD Agent",
        filters={"availability_expires_on": ["<=", now_datetime()]},
        pluck="name",
    )
    # a savepoint per agent: a failure only undoes that agent and the rest
    # still reset, without committing mid-job
    for name in agents:
        try:
            frappe.db.savepoint("expire_availability")
            frappe.get_doc("HD Agent", name).expire_availability()
        except Exception:
            frappe.db.rollback(save_point="expire_availability")
            frappe.log_error(
                title="Could not clear an expired agent status",
                reference_doctype="HD Agent",
                reference_name=name,
            )


@frappe.whitelist()
def update_agent_role(user: str, new_role: str):
    """
    Update the role of the user to Agent
    """
    frappe.only_for(("Agent Manager", "System Manager"))

    user_doc = frappe.get_doc("User", user)

    if new_role == "Manager":
        user_doc.append_roles("Agent Manager", "System Manager")
    if new_role == "Agent":
        user_doc.append_roles("Agent")
        if "Agent Manager" in frappe.get_roles(user_doc.name):
            user_doc.remove_roles("Agent Manager", "System Manager")

    user_doc.save()
