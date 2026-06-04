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
    statuses = frappe.get_all(
        "HD Agent Status",
        filters={"enable": 1},
        fields=["agent_status", "order"],
    )
    statuses.sort(key=lambda s: s.order or 0)
    return [s.agent_status for s in statuses]


def _agent_name_for_session() -> str | None:
    return frappe.db.get_value("HD Agent", {"user": frappe.session.user}, "name")


@frappe.whitelist()
@agent_only
def get_my_availability() -> dict:
    name = _agent_name_for_session()
    values = (
        frappe.db.get_value(
            "HD Agent",
            name,
            ["availability", "availability_changed_on"],
            as_dict=True,
        )
        if name
        else None
    )
    return {
        "availability": values.availability if values else None,
        "availability_changed_on": values.availability_changed_on if values else None,
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

    frappe.db.set_value(
        "HD Agent",
        name,
        {"availability": availability, "availability_changed_on": frappe.utils.now()},
    )
    return {"availability": availability}
