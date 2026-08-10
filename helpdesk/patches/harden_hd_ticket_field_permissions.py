import frappe
from frappe.permissions import add_permission, update_permission_property

# level -> role -> has write access at that level. Level 1 holds the
# customer-visible operational fields, level 2 the agent-only internals,
# level 3 the System Manager-only fields.
LEVEL_GRANTS = {
    1: {
        "System Manager": 1,
        "Agent": 1,
        "Agent Manager": 1,
        "HD Customer": 0,
        "HD Customer Manager": 0,
    },
    2: {
        "System Manager": 1,
        "Agent": 1,
        "Agent Manager": 1,
    },
    3: {
        "System Manager": 1,
    },
}


def execute():
    mirror_permlevel_grants_into_custom_docperms()


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
