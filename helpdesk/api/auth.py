import frappe

from helpdesk.utils import agent_only, get_agents_team
from helpdesk.utils import is_agent as _is_agent


@frappe.whitelist()
def get_user():
    current_user = frappe.session.user
    filters = {"name": current_user}
    fields = [
        "first_name",
        "full_name",
        "name",
        "user_image",
        "username",
        "time_zone",
        "language",
    ]
    user = frappe.get_value(
        doctype="User",
        filters=filters,
        fieldname=fields,
        as_dict=True,
    )

    is_agent = _is_agent()
    is_admin = ("System Manager" or "Admistrator") in frappe.get_roles(current_user)
    has_desk_access = is_agent or is_admin
    user_image = user.user_image
    user_first_name = user.first_name
    user_name = user.full_name
    user_id = user.name
    username = user.username
    is_manager = ("Agent Manager") in frappe.get_roles(current_user)
    user_team = get_agents_team()
    user_team_names = [team["team_name"] for team in user_team]
    language = user.language or frappe.db.get_single_value(
        "System Settings", "language"
    )

    return {
        "has_desk_access": has_desk_access,
        "is_admin": is_admin,
        "is_agent": is_agent,
        "user_id": user_id,
        "is_manager": is_manager,
        "user_image": user_image,
        "user_first_name": user_first_name,
        "user_name": user_name,
        "username": username,
        "time_zone": user.time_zone,
        "user_teams": user_team_names,
        "language": language,
    }


@frappe.whitelist()
@agent_only
def get_current_user_email_info():
    user = frappe.session.user

    email_signature, email = frappe.db.get_value(
        "User", user, ["email_signature", "email"]
    )
    user_emails = frappe.db.get_all(
        "User Email",
        filters={"parent": user},
        fields=["email_account", "email_id"],
    )
    outgoing_account_names = frappe.db.get_all(
        "Email Account",
        filters={"enable_outgoing": 1},
        pluck="name",
    )

    outgoing_emails = [
        row for row in user_emails if row.email_account in outgoing_account_names
    ]

    available_emails = frappe.db.get_all(
        "Email Account",
        filters={"enable_outgoing": 1},
        fields=["name", "email_id"],
    )

    return {
        "email_signature": email_signature,
        "email": email,
        "outgoing_emails": outgoing_emails,
        "available_emails": available_emails,
    }
