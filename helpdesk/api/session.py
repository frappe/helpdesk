import frappe

from helpdesk.utils import agent_only


@frappe.whitelist()
@agent_only
def get_users():
    session_user = frappe.session.user

    # Fetch agent-related roles in a single query
    roles_map = {}
    role_rows = frappe.qb.get_query(
        "Has Role",
        fields=["parent", "role"],
        filters={
            "parenttype": "User",
            "role": ["in", ["Agent Manager", "Agent", "Guest"]],
        },
    ).run()

    # Role priority: Manager > Agent > Guest
    priority = {"Agent Manager": 3, "Agent": 2, "Guest": 1}
    label = {"Agent Manager": "Manager", "Agent": "Agent", "Guest": "Guest"}
    for parent, role in role_rows:
        if priority.get(role, 0) > priority.get(roles_map.get(parent), 0):
            roles_map[parent] = role

    # Fetch all active users
    users = frappe.qb.get_query(
        "User",
        fields=[
            "name",
            "email",
            "enabled",
            "user_image",
            "full_name",
            "user_type",
        ],
        filters={"enabled": 1},
        order_by="full_name asc",
    ).run(as_dict=True)

    # Add role and session user information
    for u in users:
        r = roles_map.get(u["name"])
        if r:
            u["role"] = label[r]
        if u["name"] == session_user:
            u["session_user"] = True

    return users
