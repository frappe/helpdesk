import frappe


def execute():
    """Set the default agent status in HD Settings.

    Same query as the old code (newest enabled Active status) so nothing
    changes for the site after upgrade. The second query is a fallback for
    sites with no enabled Active status, the field is mandatory so it
    cannot stay empty.
    """
    if frappe.db.get_single_value("HD Settings", "default_agent_status"):
        return

    default_status = frappe.db.get_value(
        "HD Agent Status",
        {"category": "Active", "enabled": 1},
        "name",
        order_by="creation desc",
    ) or frappe.db.get_value(
        "HD Agent Status", {"enabled": 1}, "name", order_by="creation desc"
    )

    if default_status:
        frappe.db.set_single_value(
            "HD Settings", "default_agent_status", default_status
        )
