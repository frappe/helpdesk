import frappe


def execute():
    """The studio app at /kb replaces the old customer portal as the landing page."""
    # db writes rather than save: a Portal Settings save validates the portal
    # menu rows, and a stale row would fail the whole migration (see
    # setup.install.set_portal_defaults).
    home = frappe.db.get_single_value("Portal Settings", "default_portal_home")
    if home == "/helpdesk":
        frappe.db.set_single_value("Portal Settings", "default_portal_home", "/kb")

    for role_name in ("HD Customer", "HD Customer Manager"):
        if frappe.db.get_value("Role", role_name, "home_page") == "/helpdesk":
            frappe.db.set_value("Role", role_name, "home_page", "/kb")
