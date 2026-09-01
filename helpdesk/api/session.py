import frappe

from helpdesk.utils import agent_only


@frappe.whitelist()
@agent_only
def get_users():
    session_user = frappe.session.user

    # Fetch agent-related roles in a single query
    role_rows = frappe.db.get_all(
        "Has Role",
        filters={
            "parenttype": "User",
            "role": ["in", ["Agent Manager", "Agent", "Guest"]],
        },
        fields=["parent", "role"],
    )

    # Role priority: Manager > Agent > Guest
    priority = {"Agent Manager": 3, "Agent": 2, "Guest": 1}
    label = {"Agent Manager": "Manager", "Agent": "Agent", "Guest": "Guest"}
    roles_map = {}
    for row in role_rows:
        if priority.get(row.role, 0) > priority.get(roles_map.get(row.parent), 0):
            roles_map[row.parent] = row.role

    # Fetch active desk users (agents + system users). Website Users, i.e.
    # customer contacts, are intentionally excluded: this endpoint only powers
    # agent/name/avatar lookups in the desk, and on contact-heavy sites the
    # unfiltered query returned the entire (potentially 100k+ row) User table.
    users = frappe.db.get_all(
        "User",
        filters={"enabled": 1, "user_type": "System User"},
        fields=["name", "email", "enabled", "user_image", "full_name", "user_type"],
        order_by="full_name asc",
    )

    # Add role and session user information
    for u in users:
        r = roles_map.get(u.name)
        if r:
            u["role"] = label[r]
        if u.name == session_user:
            u["session_user"] = True

    return users
