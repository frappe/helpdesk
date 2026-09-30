import frappe
from frappe import _
from frappe.realtime import get_website_room

from helpdesk.utils import agent_manager_only, is_agent_manager

BANNERS = {
    "customer_portal_permission": "show_customer_portal_permission_notice",
    "ticket_field_permission": "show_ticket_field_permission_notice",
}


@frappe.whitelist()
def get_banners() -> list[str]:
    if not is_agent_manager():
        return []

    return [
        banner
        for banner, flag in BANNERS.items()
        if frappe.db.get_single_value("HD Settings", flag)
    ]


@frappe.whitelist(methods=["POST"])
@agent_manager_only
def dismiss_banner(banner: str) -> None:
    if banner not in BANNERS:
        frappe.throw(_("Unknown banner {0}").format(banner))

    frappe.db.set_single_value("HD Settings", BANNERS[banner], 0)
    frappe.publish_realtime(
        "helpdesk:settings-updated", room=get_website_room(), after_commit=True
    )
