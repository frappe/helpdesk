import frappe
from frappe.permissions import add_permission, update_permission_property

from helpdesk.consts import DEFAULT_TICKET_TEMPLATE, TICKET_INTERNAL_FIELD_PERMLEVEL

# level -> role -> has write access at that level. Level 7 holds the
# customer-visible operational fields and level 8 the agent-only internals.
# High numbers avoid colliding with permlevel schemes a site may have built
# itself.
LEVEL_GRANTS = {
    7: {
        "System Manager": 1,
        "Agent": 1,
        "Agent Manager": 1,
        "HD Customer": 0,
        "HD Customer Manager": 0,
    },
    8: {
        "System Manager": 1,
        "Agent": 1,
        "Agent Manager": 1,
    },
}


def execute():
    remember_bases_and_hide_hidden_custom_fields()
    mirror_permlevel_grants_into_custom_docperms()


def remember_bases_and_hide_hidden_custom_fields():
    """Default template rows record the level their custom field held before
    the sync existed, and rows already hidden get raised to the internal
    level once. Raise only: a migration must never expose a field."""
    rows = frappe.get_all(
        "HD Ticket Template Field",
        filters={
            "parenttype": "HD Ticket Template",
            "parent": DEFAULT_TICKET_TEMPLATE,
        },
        fields=["name", "fieldname", "hide_from_customer", "base_permlevel"],
    )
    moved = False
    for row in rows:
        custom_field = frappe.db.get_value(
            "Custom Field", {"dt": "HD Ticket", "fieldname": row.fieldname}
        )
        if not custom_field:
            continue
        level = frappe.db.get_value("Custom Field", custom_field, "permlevel") or 0
        if row.base_permlevel is None or row.base_permlevel < 0:
            frappe.db.set_value(
                "HD Ticket Template Field",
                row.name,
                "base_permlevel",
                level,
                update_modified=False,
            )
        if row.hide_from_customer and level < TICKET_INTERNAL_FIELD_PERMLEVEL:
            frappe.db.set_value(
                "Custom Field",
                custom_field,
                "permlevel",
                TICKET_INTERNAL_FIELD_PERMLEVEL,
            )
            moved = True
    if moved:
        frappe.clear_cache(doctype="HD Ticket")


def mirror_permlevel_grants_into_custom_docperms():
    """Any Custom DocPerm row makes Frappe ignore the JSON perms wholesale,
    so customised sites need the permlevel rows added explicitly or agents
    lose access to the protected fields."""
    existing = frappe.get_all(
        "Custom DocPerm",
        filters={"parent": "HD Ticket"},
        fields=["role", "permlevel"],
    )
    if not existing:
        return
    roles_at_zero = {row.role for row in existing if row.permlevel == 0}
    held = {(row.role, row.permlevel) for row in existing}
    for level, grants in LEVEL_GRANTS.items():
        for role, can_write in grants.items():
            if role not in roles_at_zero or (role, level) in held:
                continue
            add_permission("HD Ticket", role, permlevel=level)  # grants read
            if can_write:
                update_permission_property(
                    "HD Ticket", role, level, "write", 1, validate=False
                )
