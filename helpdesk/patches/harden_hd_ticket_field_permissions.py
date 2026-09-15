import frappe
from frappe.permissions import add_permission, update_permission_property

# level -> role -> can write. 7 holds customer-visible fields, 8 agent-only ones;
# high numbers stay clear of a site's own permlevel scheme
# if lvl: {role : 1} that means use holds write on that role
#
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

CUSTOMER_ROLES = ("HD Customer", "HD Customer Manager")
# add_permission opens read; these are the rest of what hd_ticket.json grants
CUSTOMER_BASE_PERMS = ("write", "create", "email", "print")


def execute():
    """Any Custom DocPerm row makes Frappe ignore the JSON perms, so customised
    sites need these rows written or the protected fields read as empty."""
    if not frappe.db.exists("Custom DocPerm", {"parent": "HD Ticket"}):
        return
    grant_ticket_access_to_customer_roles()
    grant_permlevel_access()


def grant_ticket_access_to_customer_roles():
    """Ensure that older customers are provided with the customer role if they dont have any and also provided
    necessary perms to create if it is missing. If customer perms exist return."""
    filters = {"parent": "HD Ticket", "role": ["in", CUSTOMER_ROLES]}
    if frappe.db.exists("Custom DocPerm", filters):
        return
    for role in CUSTOMER_ROLES:
        add_permission("HD Ticket", role)  # grants read at level 0
        for ptype in CUSTOMER_BASE_PERMS:
            update_permission_property("HD Ticket", role, 0, ptype, 1, validate=False)


def grant_permlevel_access():
    """A role reads the protected levels only if it can read the ticket itself."""
    existing = frappe.get_all(
        "Custom DocPerm",
        filters={"parent": "HD Ticket"},
        fields=["role", "permlevel"],
    )
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
