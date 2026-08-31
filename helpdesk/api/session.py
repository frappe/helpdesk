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

    # Fetch all active users
    users = frappe.db.get_all(
        "User",
        filters={"enabled": 1},
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


@frappe.whitelist()
def get_agent_avatars(agents: list[str] | str) -> dict:
    """Name and picture for the agents named, keyed by user id.

    The customer portal's ticket list has only `_assign` — bare user ids — and drew each
    assignee as an initial, while the same person appears in the ticket's own thread with
    their name and face. `get_users` cannot fill the gap: it is agent-only, and it hands
    back every user on the site.

    This answers for agents and no one else, so it tells a customer nothing the ticket
    they are already reading does not.
    """
    names = frappe.parse_json(agents) if isinstance(agents, str) else agents
    names = [name for name in dict.fromkeys(names or []) if name]
    if not names:
        return {}

    agents = frappe.get_all("HD Agent", filters={"name": ["in", names]}, pluck="name")
    if not agents:
        return {}

    return {
        user.name: {"name": user.full_name or user.name, "image": user.user_image}
        for user in frappe.get_all(
            "User",
            filters={"name": ["in", agents]},
            fields=["name", "full_name", "user_image"],
        )
    }
