import frappe
from frappe import _

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
    return


@frappe.whitelist()
@agent_only
def get_availability_options() -> list[str]:
    options = frappe.get_meta("HD Agent").get_field("availability").options or ""
    return [o.strip() for o in options.split("\n") if o.strip()]


def _agent_name_for_session() -> str | None:
    return frappe.db.get_value("HD Agent", {"user": frappe.session.user}, "name")


@frappe.whitelist()
@agent_only
def get_my_availability() -> dict:
    name = _agent_name_for_session()
    availability = (
        frappe.db.get_value("HD Agent", name, "availability") if name else None
    )
    return {
        "availability": availability,
        "options": get_availability_options(),
    }


@frappe.whitelist()
@agent_only
def set_my_availability(availability: str) -> dict:
    if availability not in get_availability_options():
        frappe.throw(_("Invalid availability"), frappe.ValidationError)

    name = _agent_name_for_session()
    if not name:
        frappe.throw(_("No HD Agent record for current user"), frappe.ValidationError)

    frappe.db.set_value("HD Agent", name, "availability", availability)
    return {"availability": availability}
