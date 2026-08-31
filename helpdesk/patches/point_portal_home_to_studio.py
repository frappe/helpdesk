import frappe


def execute():
    """The studio app at /kb replaces the old customer portal as the landing page."""
    portal_settings = frappe.get_single("Portal Settings")
    if portal_settings.default_portal_home == "/helpdesk":
        portal_settings.default_portal_home = "/kb"
        portal_settings.save()

    for role_name in ("HD Customer", "HD Customer Manager"):
        if frappe.db.get_value("Role", role_name, "home_page") == "/helpdesk":
            frappe.db.set_value("Role", role_name, "home_page", "/kb")
