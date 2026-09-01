import frappe


def execute():
    """Name the default agent status in HD Settings instead of inferring it.

    Freezes whatever the old lookup was resolving to on this site, so migrating
    changes nothing. The second branch only exists so the field's mandatory
    check can never strand a site with no enabled Active status; picking by
    ordering is fine once, here, and not at all in the runtime accessor.
    """
    if frappe.db.get_single_value("HD Settings", "default_agent_status"):
        return

    default_status = frappe.db.get_value(
        "HD Agent Status", {"category": "Active", "enabled": 1}, "name"
    ) or frappe.db.get_value("HD Agent Status", {"enabled": 1}, "name")

    if default_status:
        frappe.db.set_single_value(
            "HD Settings", "default_agent_status", default_status
        )
