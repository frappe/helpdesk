import frappe
from frappe.utils import get_system_timezone
from frappe.website.utils import get_home_page


def get_boot() -> dict:
    """In boot so the timezone is there before the first date renders."""
    return {
        "system_timezone": get_system_timezone(),
        # Read before the first render, so a private knowledge base never flashes for a guest
        "send_guest_to_login": frappe.session.user == "Guest"
        and not frappe.db.get_single_value("HD Settings", "public_knowledge_base"),
        # Frappe renders the home page at `/` instead of redirecting to it
        "home_page": "/" + get_home_page().lstrip("/"),
    }
