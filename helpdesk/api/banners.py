import frappe
from frappe import _
from frappe.realtime import get_website_room

from helpdesk.integrations.frappe_cloud import dismiss_trial, forget_trial, get_trial
from helpdesk.utils import agent_manager_only, is_agent_manager

BANNERS = {
    "customer_portal_permission": "show_customer_portal_permission_notice",
    "ticket_field_permission": "show_ticket_field_permission_notice",
}


@frappe.whitelist()
def get_banners() -> list[dict]:
    """Sidebar notices as `{"name": ...}`; one that needs data carries it under its own key.
    "customer_portal_permission", "ticket_field_permission" or "trial" (with `trial`).
    Always empty for anyone but agent managers and admins."""
    if not is_agent_manager():
        return []

    banners = [
        {"name": banner}
        for banner, flag in BANNERS.items()
        if frappe.db.get_single_value("HD Settings", flag)
    ]
    trial = get_trial()
    if trial:
        banners.append({"name": "trial", "trial": trial})
    return banners


@frappe.whitelist(methods=["POST"])
@agent_manager_only
def dismiss_banner(banner: str) -> None:
    """Hide a sidebar notice. Agent managers only.
    "trial" hides the trial card for this user for a day; "customer_portal_permission"
    or "ticket_field_permission" turns that notice off for everyone."""
    if banner == "trial":
        dismiss_trial()
        # Only this user's other tabs need to hide the card
        frappe.publish_realtime(
            "helpdesk:settings-updated", user=frappe.session.user, after_commit=True
        )
        return
    if banner not in BANNERS:
        frappe.throw(_("Unknown banner {0}").format(banner))

    frappe.db.set_single_value("HD Settings", BANNERS[banner], 0)
    frappe.publish_realtime(
        "helpdesk:settings-updated", room=get_website_room(), after_commit=True
    )


@frappe.whitelist(methods=["POST"])
@agent_manager_only
def refresh_trial() -> None:
    """Drop the cached trial, so the next `get_banners` reads it from Frappe Cloud."""
    forget_trial()
