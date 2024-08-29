import frappe


def has_app_permission():
    """Check if the user has permission to access the app."""
    if frappe.session.user == "Administrator":
        return True

    roles = frappe.get_roles()
    helpdesk_roles = ["Agent"]
    if any(role in roles for role in helpdesk_roles):
        return True

    return False
