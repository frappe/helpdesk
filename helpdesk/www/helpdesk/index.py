import frappe
from frappe import _
from frappe.boot import load_translations
from frappe.integrations.frappe_providers.frappecloud_billing import is_fc_site
from frappe.utils import cint
from frappe.utils.telemetry import capture

no_cache = 1


def get_context(context):
    csrf_token = frappe.sessions.get_csrf_token()
    frappe.db.commit()
    context = frappe._dict()
    context.csrf_token = csrf_token
    context.boot = get_boot()

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
    bootinfo = frappe._dict(
        {
            "default_route": get_default_route(),
            "site_name": frappe.local.site,
            "read_only_mode": frappe.flags.read_only,
            "favicon": get_favicon(),
            "setup_complete": cint(frappe.get_system_settings("setup_complete")),
            "is_fc_site": is_fc_site(),
        }
    )
    
    bootinfo.lang = frappe.local.lang
    load_translations(bootinfo)

    return frappe.as_json(bootinfo, indent=None, separators=(",", ":"))

def get_default_route():
    return "/helpdesk"


def get_favicon():
    return (
        frappe.db.get_single_value("Website Settings", "favicon")
        or "/assets/helpdesk/desk/favicon.svg"
    )
