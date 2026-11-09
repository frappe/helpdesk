import frappe
from frappe import _
from frappe.desk.doctype.notification_log.notification_log import (
    enqueue_create_notification,
)
from frappe.utils.user import get_users_with_role

from helpdesk.helpdesk.doctype.hd_customer.hd_customer import CUSTOMER_ROLES

# What older installs wrote to Portal Settings; on Frappe v16 it overrode every user's home page
HELPDESK_PORTAL_DEFAULTS = {
    "default_portal_home": "/helpdesk",
    "default_role": "HD Customer",
}


def execute():
    cleared_portal_settings = clear_portal_settings()
    cleared_role_home_pages = clear_role_home_pages()
    if cleared_portal_settings or cleared_role_home_pages:
        frappe.cache.delete_key("home_page")
        notify_system_managers()


def clear_portal_settings() -> bool:
    fields = get_fields_set_by_helpdesk()
    if fields:
        frappe.db.set_single_value("Portal Settings", dict.fromkeys(fields))
    return bool(fields)


def clear_role_home_pages() -> bool:
    """Administrator holds every role, so this home page took over its login too."""
    roles = frappe.get_all(
        "Role",
        filters={"name": ["in", CUSTOMER_ROLES], "home_page": "/helpdesk"},
        pluck="name",
    )
    for role in roles:
        frappe.db.set_value("Role", role, "home_page", None)
    return bool(roles)


def get_fields_set_by_helpdesk() -> list[str]:
    """Helpdesk wrote these without a Version, so a Version for the field means an admin set it."""
    hand_edited_fields = get_hand_edited_fields()
    return [
        field
        for field, value in HELPDESK_PORTAL_DEFAULTS.items()
        if field not in hand_edited_fields
        and frappe.db.get_single_value("Portal Settings", field) == value
    ]


def get_hand_edited_fields() -> set[str]:
    versions = frappe.get_all(
        "Version", filters={"ref_doctype": "Portal Settings"}, pluck="data"
    )
    return {
        change[0]
        for data in versions
        for change in frappe.parse_json(data).get("changed", [])
    }


def notify_system_managers() -> None:
    message = _(
        "Helpdesk no longer sets a site-wide portal home page or signup role. "
        "Users now land on their default app. To restore the old behavior, "
        "set Portal Settings → Default Portal Home to /helpdesk."
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
