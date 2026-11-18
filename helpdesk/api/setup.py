import frappe
from frappe import _

SETUP_ROLE = "System Manager"


def is_v2_site() -> bool:
    try:
        from frappe.integrations.frappe_providers.cloud_settings import is_v2_site
    except ImportError:
        return False
    return is_v2_site()


def is_setup_pending() -> bool:
    """The first-run setup is for a System Manager on a Frappe Cloud v2 site, until it ends."""
    return (
        SETUP_ROLE in frappe.get_roles()
        and is_v2_site()
        and not frappe.db.get_single_value("HD Settings", "setup_complete")
    )


@frappe.whitelist(methods=["POST"])
def complete_setup():
    """Ends the first-run setup, on Finish or Skip. A second call is a no-op."""
    frappe.only_for(SETUP_ROLE)
    finish_frappe_setup()
    frappe.db.set_single_value("HD Settings", "setup_complete", 1)


@frappe.whitelist(methods=["POST"])
def reset_setup():
    """Developer mode only: undoes the Framework and Helpdesk setup, so the first-run setup shows again.
    Records made during setup stay."""
    frappe.only_for(SETUP_ROLE)
    if not frappe.conf.developer_mode:
        frappe.throw(
            _("Setup can only be reset in developer mode."), frappe.PermissionError
        )
    frappe.qb.update("Installed Application").set("is_setup_complete", 0).run()
    frappe.db.set_single_value(
        "System Settings", {"setup_complete": 0, "enable_telemetry": 1}
    )
    frappe.db.set_single_value("HD Settings", "setup_complete", 0)
    frappe.clear_cache()


def finish_frappe_setup():
    """Finishes the Framework setup wizard with the values Frappe Cloud stored, as Raven does.
    Apps with wizard stages of their own, like ERPNext, still need the desk wizard."""
    from frappe.desk.page.setup_wizard.setup_wizard import setup_complete

    if (
        frappe.is_setup_complete()
        or not is_v2_site()
        or frappe.get_hooks("setup_wizard_stages")
    ):
        return
    result = setup_complete(frappe_setup_args())
    if result.get("status") != "ok":
        frappe.log_error(
            title="Helpdesk: could not finish the Framework setup wizard",
            message=result.get("fail"),
        )


def frappe_setup_args() -> dict:
    """What the wizard's first slide would send, from System Settings."""
    settings = frappe.get_single("System Settings")
    language = (
        frappe.db.get_value("Language", settings.language, "language_name") or "English"
    )
    return {
        "language": language,
        "lang": language,
        "country": settings.country,
        "timezone": settings.time_zone,
        "currency": settings.currency,
        "enable_telemetry": settings.enable_telemetry,
    }
