import frappe
from frappe import _
from frappe.integrations.frappe_providers.frappecloud_billing import is_fc_site
from frappe.utils import cint, get_system_timezone
from frappe.utils.jinja_globals import is_rtl
from frappe.utils.telemetry import capture

from helpdesk.helpdesk.doctype.hd_settings.helpers import get_customer_home_page
from helpdesk.utils import get_agent_name, is_agent

no_cache = 1


def get_context(context):
    frappe.db.commit()
    redirect_customer_home()
    context.boot = get_boot()

    # telemetry
    if frappe.session.user != "Guest":
        capture("active_site", "helpdesk")
    return context


def redirect_customer_home():
    """Customer roles keep `/helpdesk` as their home, so a user who is also an
    agent lands on the desk. Everyone else goes on to the portal from here."""
    # as `has_desk_access` in api/auth.py
    if (
        frappe.session.user == "Guest"
        or is_agent()
        or "System Manager" in frappe.get_roles()
    ):
        return
    # Deep links stay with the desk router, which sends customers to the same page on the portal
    if frappe.request.path.rstrip("/") not in ("", "/helpdesk"):
        return
    frappe.local.flags.redirect_location = get_customer_home_page()
    # 302: the target follows HD Settings and the user's roles, so browsers must not cache it
    raise frappe.Redirect(302)


@frappe.whitelist(methods=["POST"], allow_guest=True)
def get_context_for_dev():
    if not frappe.conf.developer_mode:
        frappe.throw(_("This method is only meant for developer mode"))
    return get_boot()


def get_boot():
    return frappe._dict(
        {
            "default_route": get_default_route(),
            "customer_home_page": get_customer_home_page(),
            "site_name": frappe.local.site,
            "read_only_mode": frappe.flags.read_only,
            "csrf_token": frappe.sessions.get_csrf_token(),
            "setup_complete": cint(frappe.get_system_settings("setup_complete")),
            "is_fc_site": is_fc_site(),
            "session_user": frappe.session.user,
            "agent": get_agent_name(),
            "date_format": frappe.get_system_settings("date_format"),
            "time_format": frappe.get_system_settings("time_format"),
            "default_country": frappe.db.get_default("country"),
            "timezone": {
                "system": get_system_timezone(),
                "user": frappe.db.get_value("User", frappe.session.user, "time_zone")
                or get_system_timezone(),
            },
            "lang": frappe.local.lang,
            "dir": "rtl" if is_rtl() else "ltr",
            "apps": frappe.get_installed_apps(),
            "telemetry": get_telemetry_boot(),
        }
    )


def get_default_route():
    return "/helpdesk"


def get_telemetry_boot():
    """Direct-mode config for the browser telemetry client, as a boot value.

    Telemetry must never break the page: older frappe versions have no pulse
    module, and any boot_config error degrades to "disabled". The key it
    ships is a public write-only ingest key (same as desk boot).
    """
    try:
        from frappe.utils.telemetry.pulse.client import boot_config

        return boot_config()
    except Exception:
        return {"enabled": False}
