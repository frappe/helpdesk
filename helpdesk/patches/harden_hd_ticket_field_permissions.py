import frappe
from frappe.permissions import add_permission, update_permission_property

# level -> role -> has write access at that level. Level 7 holds the
# customer-visible operational fields, level 8 the agent-only internals,
# level 9 the System Manager-only fields. High numbers avoid colliding
# with permlevel schemes a site may have built itself.
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
    9: {
        "System Manager": 1,
    },
}


def execute():
    mirror_permlevel_grants_into_custom_docperms()
    sync_template_field_permlevels()


def sync_template_field_permlevels():
    """Apply template visibility to field permlevels on existing sites
    without waiting for each template to be saved again."""
    for name in frappe.get_all("HD Ticket Template", pluck="name"):
        frappe.get_doc("HD Ticket Template", name).sync_field_permlevels()


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
