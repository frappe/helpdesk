import frappe


def has_app_permission():
    """Check if the user has permission to access the app."""
    if frappe.session.user == "Administrator":
        return True

    roles = frappe.get_roles()
    allowed_roles = ["Agent", "System Manager"]
    if any(role in roles for role in allowed_roles):
        return True

    # Customers can access the portal but not the agent desk
    if frappe.db.exists("HD Customer", {"email_id": frappe.session.user}):
        return True

    return False
