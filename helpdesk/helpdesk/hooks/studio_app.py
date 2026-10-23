import frappe
from frappe.utils import escape_html, get_system_timezone
from frappe.website.utils import get_home_page

from helpdesk.api.config import get_favicon


def get_boot() -> dict:
    """In boot so the timezone is there before the first date renders."""
    return {
        "system_timezone": get_system_timezone(),
        # The zone the customer picked in Settings, else the system's, as on the desk.
        # Guest has a zone too, set at install, which says nothing about the visitor.
        "user_timezone": (
            frappe.session.user != "Guest"
            and frappe.db.get_value("User", frappe.session.user, "time_zone")
        )
        or get_system_timezone(),
        # Read before the first render, so a private knowledge base never flashes for a guest
        "send_guest_to_login": frappe.session.user == "Guest"
        and not frappe.db.get_single_value("HD Settings", "public_knowledge_base"),
        # Frappe renders the home page at `/` instead of redirecting to it
        "home_page": "/" + get_home_page().lstrip("/"),
        # Pages put it in their tab title before get_config answers
        "brand_name": get_brand_name(),
    }


def update_website_context(context):
    """The portal shows the desk's brand name and favicon before its scripts load.
    A favicon set on the Studio app itself wins."""
    doc = context.get("doc")
    if doc and doc.doctype == "Studio App" and doc.name == "helpdesk":
        context.app_title = escape_for_shell(get_brand_name())
        context.favicon = context.favicon or escape_for_shell(get_favicon())


def escape_for_shell(value: str | None) -> str:
    """Frappe's renderer.html prints these unescaped, inside HTML and a JS string."""
    value = escape_html(value or "").replace("\\", "&#92;")
    return " ".join(value.splitlines())


def get_brand_name() -> str:
    return frappe.db.get_single_value("HD Settings", "brand_name") or "Helpdesk"
