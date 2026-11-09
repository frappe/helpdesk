import frappe

from helpdesk.helpdesk.doctype.hd_customer.hd_customer import CUSTOMER_ROLES
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
    user_doc = frappe.get_doc("User", user)
    user_doc.flags.ignore_permissions = True
    user_doc.add_roles("HD Customer")
    # portal pages are GET requests, which Frappe rolls back
    frappe.db.commit()


def is_helpdesk_only_app() -> bool:
    apps = {app.get("name") for app in frappe.get_hooks("add_to_apps_screen")}
    return apps - {"frappe"} == {"helpdesk"}


def is_website_user(user: str) -> bool:
    return frappe.db.get_value("User", user, "user_type") == "Website User"


def has_customer_role(user: str) -> bool:
    return bool(set(CUSTOMER_ROLES) & set(frappe.get_roles(user)))
