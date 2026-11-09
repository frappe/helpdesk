import frappe
from frappe.utils.user import is_website_user

from helpdesk.helpdesk.doctype.hd_customer.hd_customer import (
    CUSTOMER_ROLES,
    has_customer_role,
)
from helpdesk.utils import CUSTOMER_PORTAL_ROOT, is_agent


def get_website_user_home_page(user: str) -> str | None:
    """Customers land on the portal; agents only on a site that runs Helpdesk alone, elsewhere the default app decides."""
    if user == "Guest":
        return None
    if is_website_user(user):
        if has_customer_role(user) or is_helpdesk_only_app():
            return CUSTOMER_PORTAL_ROOT
        return None
    if is_agent(user) and is_helpdesk_only_app():
        return "/helpdesk"


def grant_customer_role(user: str) -> None:
    """Self-signups become customers on their first portal visit, not at signup on every portal."""
    if user == "Guest" or not is_website_user(user) or has_customer_role(user):
        return
    # lock the user, so a first visit from two tabs adds the role once
    frappe.db.get_value("User", user, "name", for_update=True)
    if frappe.db.exists(
        "Has Role",
        {"parenttype": "User", "parent": user, "role": ["in", CUSTOMER_ROLES]},
    ):
        return
    add_customer_role(user)


def add_customer_role(user: str) -> None:
    """A failed save must not take the portal down with it; the next visit tries again."""
    user_doc = frappe.get_doc("User", user)
    user_doc.flags.ignore_permissions = True
    try:
        user_doc.add_roles("HD Customer")
    except Exception:
        frappe.db.rollback()
        frappe.log_error(
            title="Could not grant the HD Customer role", defer_insert=True
        )
        return
    # portal pages are GET requests, which Frappe rolls back unless asked to commit
    frappe.local.flags.commit = True


def is_helpdesk_only_app() -> bool:
    apps = {app.get("name") for app in frappe.get_hooks("add_to_apps_screen")}
    return apps - {"frappe"} == {"helpdesk"}
