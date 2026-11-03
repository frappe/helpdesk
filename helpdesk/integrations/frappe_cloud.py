"""Frappe Cloud v2: boot context and the site's free trial, through Frappe's Cloud Settings."""

import time

import frappe

try:
    from frappe.integrations.frappe_providers import cloud_settings
except ImportError:  # a Frappe without Cloud Settings
    cloud_settings = None

# Days left change once a day, and each read goes through Pilot and Central uncached
TRIAL_CACHE_SECONDS = 6 * 60 * 60
# A failed read retries sooner, so a site whose trial ended is not left without the card
TRIAL_RETRY_SECONDS = 5 * 60
TRIAL_DISMISS_SECONDS = 24 * 60 * 60
TRIAL_CACHE_KEY = "helpdesk:trial"
TRIAL_DISMISSED_KEY = "helpdesk:trial-dismissed"


def get_boot_context() -> dict:
    """Cloud Settings context for boot; enabled only for System Managers on a v2 site."""
    if not cloud_settings:
        return {"enabled": False}
    return cloud_settings.get_boot_context()


def get_trial() -> dict | None:
    """The site's open trial, unless this user dismissed it. A failed read keeps the last one."""
    if not cloud_settings or not cloud_settings.is_cloud_settings_enabled():
        return None

    cached = frappe.cache.get_value(TRIAL_CACHE_KEY) or {"trial": None, "refresh_at": 0}
    if time.time() >= cached.get("refresh_at", 0):
        cached = _read_trial(cached["trial"])
        frappe.cache.set_value(TRIAL_CACHE_KEY, cached)

    trial = cached["trial"]
    # An ended trial cannot be dismissed
    if trial and trial.get("state") != "Ended" and is_trial_dismissed():
        return None
    return trial


def _read_trial(last_trial: dict | None) -> dict:
    try:
        trial = cloud_settings.get_billing().get("trial")
    except Exception:
        # get_billing throws, which also queues its message for the response
        frappe.clear_last_message()
        frappe.log_error(title="Trial card: could not read billing")
        return {"trial": last_trial, "refresh_at": time.time() + TRIAL_RETRY_SECONDS}
    return {"trial": trial, "refresh_at": time.time() + TRIAL_CACHE_SECONDS}


def forget_trial() -> None:
    """Read the trial again on the next request, e.g. after the user changed the plan."""
    frappe.cache.delete_value(TRIAL_CACHE_KEY)


def dismiss_trial() -> None:
    frappe.cache.set_value(
        TRIAL_DISMISSED_KEY,
        1,
        user=frappe.session.user,
        expires_in_sec=TRIAL_DISMISS_SECONDS,
    )


def is_trial_dismissed() -> bool:
    return bool(
        frappe.cache.get_value(
            TRIAL_DISMISSED_KEY, user=frappe.session.user, expires=True
        )
    )
