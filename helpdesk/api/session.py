import frappe

from helpdesk.utils import agent_only


@frappe.whitelist()
@agent_only
def get_users(page_length: int = 100, start: int = 0):
    """Get list of users with their helpdesk roles."""
    page_length = min(int(page_length or 100), 500)
    start = max(int(start or 0), 0)

    users = frappe.qb.get_query(
        "User",
        fields=["name", "email", "enabled", "user_image", "full_name", "user_type"],
        order_by="full_name asc",
        distinct=True,
    ).limit(page_length).offset(start).run(as_dict=1)

    for user in users:
        roles = frappe.get_roles(user.name)
        if "Agent Manager" in roles:
            user.role = "Manager"
        elif "Agent" in roles:
            user.role = "Agent"
        elif "Guest" in roles:
            user.role = "Guest"
        if frappe.session.user == user.name:
            user.session_user = True

    return users
