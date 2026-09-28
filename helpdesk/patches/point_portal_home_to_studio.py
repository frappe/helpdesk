import frappe

from helpdesk.helpdesk.doctype.hd_customer.hd_customer import CUSTOMER_ROLES
from helpdesk.utils import CUSTOMER_PORTAL_ROOT


def execute():
    """The studio app replaces the old customer portal as the landing page."""
    # db writes, not save: a stale Portal Settings menu row would fail the migration.
    portal_home = frappe.db.get_single_value("Portal Settings", "default_portal_home")
    if portal_home == "/helpdesk":
        frappe.db.set_single_value(
            "Portal Settings", "default_portal_home", CUSTOMER_PORTAL_ROOT
        )
    frappe.db.set_value(
        "Role",
        {"name": ["in", CUSTOMER_ROLES], "home_page": "/helpdesk"},
        "home_page",
        CUSTOMER_PORTAL_ROOT,
    )
