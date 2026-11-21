from urllib.parse import urlparse

import frappe
from frappe.apps import get_default_app
from frappe.model.document import Document
from frappe.utils import has_common
from frappe.utils.user import is_website_user

from helpdesk.helpdesk.doctype.hd_customer.hd_customer import (
    CUSTOMER_ROLES,
    has_customer_role,
)
from helpdesk.utils import AGENT_PORTAL_ROOT, CUSTOMER_PORTAL_ROOT, has_desk_access


def get_website_user_home_page(user: str) -> str | None:
    """Customers land on the portal. Agents land on the desk when Helpdesk is the only app or their default app."""
    if user == "Guest":
        return None
    if is_website_user(user):
        if has_customer_role(user) or is_helpdesk_only_app():
            return CUSTOMER_PORTAL_ROOT
        return None
    if has_desk_access(user) and (
        is_helpdesk_only_app() or get_default_app() == "helpdesk"
    ):
        return AGENT_PORTAL_ROOT


def grant_customer_role_on_signup(user_doc: Document, method=None) -> None:
    """Helpdesk sends signups to /login?redirect-to=/helpdesk, and Frappe's signup passes it on."""
    redirect_to = frappe.form_dict.get("redirect_to")
    if user_doc.user_type == "Website User" and is_helpdesk_path(redirect_to):
        user_doc.append_roles("HD Customer")


def is_helpdesk_path(path: str | None) -> bool:
    path = urlparse(path or "").path
    return any(
        path == root or path.startswith(root + "/")
        for root in (CUSTOMER_PORTAL_ROOT, AGENT_PORTAL_ROOT)
    )


def grant_customer_role(user: str) -> None:
    """For OAuth signups: their redirect-to never reaches the User hooks, so the first portal visit adds the role."""
    if user == "Guest" or not is_website_user(user) or has_customer_role(user):
        return
    # lock the user, so a first visit from two tabs adds the role once
    user_doc = frappe.get_doc("User", user, for_update=True)
    if has_common(CUSTOMER_ROLES, [row.role for row in user_doc.roles]):
        return
    add_customer_role(user_doc)


def add_customer_role(user_doc: Document) -> None:
    """A failed save must not take the portal down with it; the next visit tries again."""
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
