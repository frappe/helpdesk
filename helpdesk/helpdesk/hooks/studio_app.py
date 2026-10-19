import frappe
from frappe.utils import get_system_timezone

from helpdesk.api.config import get_favicon


def get_boot() -> dict:
    """`window.boot` for the portal, there before its first date renders."""
    return {
        "system_timezone": get_system_timezone(),
        # Shown before get_config answers
        "brand_name": get_brand_name(),
    }


def update_website_context(context):
    """The portal shows the desk's brand name and favicon before its scripts load.
    A favicon set on the Studio app itself wins."""
    doc = context.get("doc")
    if doc and doc.doctype == "Studio App" and doc.name == "helpdesk":
        context.app_title = get_brand_name()
        context.favicon = context.favicon or get_favicon()


def get_brand_name() -> str:
    return frappe.db.get_single_value("HD Settings", "brand_name") or "Helpdesk"
