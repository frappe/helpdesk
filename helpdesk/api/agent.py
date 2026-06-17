import frappe
from frappe import _

from helpdesk.utils import agent_only, get_agent_name, publish_event


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
    return frappe.get_all(
        "HD Agent Status",
        filters={"enable": 1},
        order_by="`tabHD Agent Status`.status_order asc",
        pluck="agent_status",
    )


@frappe.whitelist()
@agent_only
def get_my_availability() -> dict:
    name = get_agent_name()
    values = (
        frappe.db.get_value(
            "HD Agent",
            name,
            ["availability", "availability_changed_on"],
            as_dict=True,
        )
        if name
        else {}
    ) or {}
    return {
        "availability": values.get("availability"),
        "availability_changed_on": values.get("availability_changed_on"),
        "options": get_availability_options(),
    }


@frappe.whitelist()
@agent_only
def set_my_availability(availability: str) -> dict:
    if not frappe.db.exists("HD Agent Status", {"name": availability, "enable": 1}):
        frappe.throw(_("Invalid availability"), frappe.ValidationError)

    name = get_agent_name()
    if not name:
        frappe.throw(_("No HD Agent record for current user"), frappe.ValidationError)

    changed_on = frappe.utils.now()
    frappe.db.set_value(
        "HD Agent",
        name,
        {"availability": availability, "availability_changed_on": changed_on},
    )
    publish_event(
        "agent_availability_updated",
        data={
            "agent": name,
            "availability": availability,
            "availability_changed_on": changed_on,
        },
    )
    return {"availability": availability}
