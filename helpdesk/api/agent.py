import frappe

from helpdesk.utils import agent_only


@frappe.whitelist()
@agent_only
def sent_invites(emails: list[str], send_welcome_mail_to_user: bool = True):
    for email in emails:
        if frappe.db.exists("User", email):
            user = frappe.get_doc("User", email)
        else:
            user = frappe.get_doc(
                {"doctype": "User", "email": email, "first_name": email.split("@")[0]}
            ).insert()

            if send_welcome_mail_to_user:
                user.send_welcome_mail_to_user()

        frappe.get_doc(
            {
                "doctype": "HD Agent",
                "ID": email,
                "user": user.name,
                "agent_name": user.full_name,
                "user_image": user.user_image,
            }
        ).insert()
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

