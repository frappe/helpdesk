import frappe


ALLOWED_APP_ROLES = {"Agent", "Agent Manager", "System Manager"}


def has_app_permission():
    """Check if the user has permission to access the app."""
    if frappe.session.user == "Administrator":
        return True

    return bool(ALLOWED_APP_ROLES.intersection(frappe.get_roles()))
