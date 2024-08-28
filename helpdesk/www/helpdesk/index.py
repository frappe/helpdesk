import frappe
from frappe import _
from frappe.utils.telemetry import capture

from helpdesk import __version__

no_cache = 1


def get_context(context):
    context.csrf_token = frappe.sessions.get_csrf_token()
    context.frappe_version = frappe.__version__
    context.helpdesk_version = __version__
    context.site_name = frappe.local.site
    # website favicon
    context.favicon = get_favicon()
    frappe.db.commit()

    # telemetry
    if frappe.session.user != "Guest":
        capture("active_site", "helpdesk")
    return context


@frappe.whitelist(methods=["POST"], allow_guest=True)
def get_context_for_dev():
    if not frappe.conf.developer_mode:
        frappe.throw(_("This method is only meant for developer mode"))
    return get_boot()


def get_boot():
    return frappe._dict(
        {
            "frappe_version": frappe.__version__,
            "default_route": get_default_route(),
            "site_name": frappe.local.site,
            "read_only_mode": frappe.flags.read_only,
            "csrf_token": frappe.sessions.get_csrf_token(),
            "favicon": get_favicon(),
        }
    )


def get_default_route():
    return "/helpdesk"


def get_favicon():
    return (
        frappe.db.get_single_value("Website Settings", "favicon")
        or "/assets/helpdesk/desk/favicon.svg"
    )
