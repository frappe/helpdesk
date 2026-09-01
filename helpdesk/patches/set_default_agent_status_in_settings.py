import frappe


def execute():
    """Name the default agent status in HD Settings instead of inferring it.

    Deliberately reproduces the lookup this replaces, ordering and all, so a
    site with several enabled Active statuses freezes the one it was already
    resolving to and upgrading changes nothing. `creation desc` is what the old
    frappe.db.get_value resolved its default ordering to; spelled out here
    because the whole point of the change is that nobody should have to know
    that. Picking by ordering is fine once, at migration time, and not at all
    in the runtime accessor.

    The fallback only exists so the field's mandatory check cannot strand a
    site that has no enabled Active status at all.
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
