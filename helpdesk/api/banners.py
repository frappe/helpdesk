import time

import frappe
from frappe import _
from frappe.realtime import get_website_room

from helpdesk.utils import agent_manager_only, is_agent_manager

BANNERS = {
    "customer_portal_permission": "show_customer_portal_permission_notice",
    "ticket_field_permission": "show_ticket_field_permission_notice",
}

# Days left change once a day, and each read goes through Pilot and Central uncached
TRIAL_CACHE_SECONDS = 6 * 60 * 60
TRIAL_DISMISS_SECONDS = 24 * 60 * 60
TRIAL_CACHE_KEY = "helpdesk:trial"
TRIAL_DISMISSED_KEY = "helpdesk:trial-dismissed"


@frappe.whitelist()
def get_banners() -> list[dict]:
    """The notices the sidebar shows, as `{"name": ...}`. The trial card carries its `trial`."""
    if not is_agent_manager():
        return []

    banners = [
        {"name": banner}
        for banner, flag in BANNERS.items()
        if frappe.db.get_single_value("HD Settings", flag)
    ]
    trial = get_trial()
    if trial and not is_trial_dismissed(trial):
        banners.append({"name": "trial", "trial": trial})
    return banners


@frappe.whitelist(methods=["POST"])
@agent_manager_only
def dismiss_banner(banner: str) -> None:
    if banner == "trial":
        frappe.cache.set_value(
            TRIAL_DISMISSED_KEY,
            1,
            user=frappe.session.user,
            expires_in_sec=TRIAL_DISMISS_SECONDS,
        )
        return
    if banner not in BANNERS:
        frappe.throw(_("Unknown banner {0}").format(banner))

    frappe.db.set_single_value("HD Settings", BANNERS[banner], 0)
    frappe.publish_realtime(
        "helpdesk:settings-updated", room=get_website_room(), after_commit=True
    )


def get_trial() -> dict | None:
    """The site's open Frappe Cloud trial, for System Managers on a v2 site.

    Cached per site. The card is only a reminder, so when billing can't be read
    the last known trial stays until the next refresh.
    """
    try:
        from frappe.integrations.frappe_providers import cloud_settings
    except ImportError:
        return None
    if not cloud_settings.is_cloud_settings_enabled():
        return None

    cached = frappe.cache.get_value(TRIAL_CACHE_KEY) or {"trial": None, "fetched_at": 0}
    if time.time() - cached["fetched_at"] > TRIAL_CACHE_SECONDS:
        try:
            cached["trial"] = cloud_settings.get_billing().get("trial")
        except Exception:
            # get_billing throws, which also queues its message for the response
            frappe.clear_last_message()
            frappe.log_error(title="Trial card: could not read billing")
        cached["fetched_at"] = time.time()
        frappe.cache.set_value(TRIAL_CACHE_KEY, cached)
    return cached["trial"]


def is_trial_dismissed(trial: dict) -> bool:
    # An ended trial cannot be dismissed
    if trial.get("state") == "Ended":
        return False
    return bool(
        frappe.cache.get_value(
            TRIAL_DISMISSED_KEY, user=frappe.session.user, expires=True
        )
    )
