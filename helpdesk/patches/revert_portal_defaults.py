import frappe
from frappe import _
from frappe.desk.doctype.notification_log.notification_log import (
    enqueue_create_notification,
)
from frappe.utils.user import get_users_with_role

from helpdesk.helpdesk.doctype.hd_customer.hd_customer import CUSTOMER_ROLES

HELPDESK_PORTAL_DEFAULTS = {
    "default_portal_home": "/helpdesk",
    "default_role": "HD Customer",
}
HELPDESK_ROLE_HOME_PAGE = "/helpdesk"


def execute():
    """Older installs sent every user to /helpdesk after login.
    Clears only the values that still match what Helpdesk wrote."""
    cleared_portal_settings = clear_portal_settings()
    cleared_role_home_pages = clear_role_home_pages()
    if cleared_portal_settings or cleared_role_home_pages:
        frappe.cache.delete_key("home_page")
        notify_system_managers()


def clear_portal_settings() -> bool:
    """Early installs saved these with a Version, so the value is the only reliable sign."""
    current = frappe.db.get_singles_dict("Portal Settings")
    fields = [
        field
        for field, value in HELPDESK_PORTAL_DEFAULTS.items()
        if current.get(field) == value
    ]
    if fields:
        frappe.db.set_single_value("Portal Settings", dict.fromkeys(fields))
    return bool(fields)


def clear_role_home_pages() -> bool:
    """Administrator holds every role, so this home page took over its login too."""
    roles = frappe.get_all(
        "Role",
        filters={"name": ["in", CUSTOMER_ROLES], "home_page": HELPDESK_ROLE_HOME_PAGE},
        pluck="name",
    )
    for role in roles:
        frappe.db.set_value("Role", role, "home_page", None)
    return bool(roles)


def notify_system_managers() -> None:
    message = _(
        "Helpdesk no longer sends every user to /helpdesk after login. "
        "Users now land on their default app. Agents who want Helpdesk as their "
        "home can set Helpdesk as their default app."
    )
    enqueue_create_notification(
        get_users_with_role("System Manager"),
        {
            "type": "Alert",
            "subject": message,
            "document_type": "Portal Settings",
            "document_name": "Portal Settings",
        },
    )
