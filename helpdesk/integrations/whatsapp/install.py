"""Idempotent setup for the WhatsApp integration.

Called from ``after_install``/``after_migrate``. Every step is a no-op when the
frappe_whatsapp transport app is absent, so Helpdesk installs cleanly without
it. The steps: extend ``WhatsApp Message`` with the ``hd_ticket`` link, and
grant the WhatsApp DocTypes to the agent roles.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.permissions import add_permission, update_permission_property

from helpdesk.integrations.whatsapp.utils import WHATSAPP_MESSAGE

WHATSAPP_DOCTYPES = (WHATSAPP_MESSAGE, "WhatsApp Templates", "WhatsApp Settings")
WHATSAPP_ROLES = ("Agent", "Agent Manager")
WHATSAPP_PERMS = (
    "read",
    "write",
    "create",
    "delete",
    "share",
    "email",
    "print",
    "report",
    "export",
)


def _transport_installed() -> bool:
    """Whether the frappe_whatsapp DocTypes exist.

    Uses the same predicate as the runtime API (DocType existence, not
    ``get_installed_apps``) so setup and API never disagree during the window
    where the app is listed but not yet migrated, or leaves orphan DocTypes.
    """
    return bool(frappe.db.exists("DocType", WHATSAPP_MESSAGE))


def add_custom_fields() -> None:
    """Add the ``hd_ticket`` link that records which ticket a message came from.

    The conversation stays anchored on the Contact (omnichannel); this optional
    link is what lets the UI narrow the thread to a single ticket. Owned by
    Helpdesk as a Custom Field so the frappe_whatsapp app is never forked.
    """
    if not _transport_installed():
        return

    create_custom_fields(
        {
            "WhatsApp Message": [
                {
                    "fieldname": "hd_ticket",
                    "label": "HD Ticket",
                    "fieldtype": "Link",
                    "options": "HD Ticket",
                    "insert_after": "reference_name",
                    "read_only": 1,
                    "no_copy": 1,
                    "search_index": 1,
                }
            ]
        },
        ignore_validate=True,
    )


def add_roles() -> None:
    if not _transport_installed():
        return

    for doctype in WHATSAPP_DOCTYPES:
        if not frappe.db.exists("DocType", doctype):
            continue
        for role in WHATSAPP_ROLES:
            if not frappe.db.exists("Role", role):
                continue
            # Ensure the level-0 perm row exists, then (re)grant each property.
            # Idempotent per property rather than skipping the whole grant when
            # a row is already present — a pre-seeded read-only perm must still
            # gain write/create, or agents can read but never send.
            if not frappe.db.exists(
                "Custom DocPerm",
                {"parent": doctype, "role": role, "permlevel": 0},
            ):
                add_permission(doctype, role, 0)
            for prop in WHATSAPP_PERMS:
                update_permission_property(doctype, role, 0, prop, 1)
