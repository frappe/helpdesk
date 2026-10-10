import frappe

from helpdesk.helpdesk.doctype.hd_customer.hd_customer import CUSTOMER_ROLES
from helpdesk.utils import CUSTOMER_PORTAL_ROOT

# The old customer portal, and the studio portal's first root before it moved to /help.
OLD_HOMES = ("/helpdesk", "/kb")


def execute():
    """The studio app replaces the old customer portal as the landing page."""
    # db writes, not save: a stale Portal Settings menu row would fail the migration.
    portal_home = frappe.db.get_single_value("Portal Settings", "default_portal_home")
    if portal_home in OLD_HOMES:
        frappe.db.set_single_value(
            "Portal Settings", "default_portal_home", CUSTOMER_PORTAL_ROOT
        )
    frappe.db.set_value(
        "Role",
        {"name": ["in", CUSTOMER_ROLES], "home_page": ["in", OLD_HOMES]},
        "home_page",
        CUSTOMER_PORTAL_ROOT,
    )
    # Invitations sent while the portal sat at /kb would land on a dead path.
    for name, path in frappe.get_all(
        "User Invitation",
        filters=[["redirect_to_path", "like", "/kb%"]],
        fields=["name", "redirect_to_path"],
        as_list=True,
    ):
        if path == "/kb" or path.startswith("/kb/"):
            frappe.db.set_value(
                "User Invitation",
                name,
                "redirect_to_path",
                CUSTOMER_PORTAL_ROOT + path.removeprefix("/kb"),
            )
