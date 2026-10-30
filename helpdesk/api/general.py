import frappe
from frappe.translate import get_all_translations


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_translations():
    """All translations for the current user's language, as a dict.
    Uses the system language for guests and users without one. Open to guests."""
    language = None
    if frappe.session.user != "Guest":
        language = frappe.db.get_value("User", frappe.session.user, "language")
    if not language:
        language = frappe.db.get_single_value("System Settings", "language")
    return get_all_translations(language)
