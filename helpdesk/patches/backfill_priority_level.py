import frappe

BUILTIN_LEVELS = ("Urgent", "High", "Medium", "Low")


def execute():
    """Backfill the `level` field on HD Ticket Priority.

    Builtins map to their own name. Custom priorities inherit the level of the
    nearest builtin ranked above them, walking most-urgent-first. Sites with no
    builtin priorities have no anchor, so everything falls back to Medium.
    """
    if "integer_value" not in frappe.db.get_table_columns("HD Ticket Priority"):
        # Fresh install already seeds `level`; there is nothing to migrate.
        return

    # Lower integer_value = higher priority, so ascending walks most urgent first.
    priorities = frappe.get_all(
        "HD Ticket Priority", order_by="integer_value asc", pluck="name"
    )

    has_anchor = any(name in BUILTIN_LEVELS for name in priorities)
    current_level = "Urgent" if has_anchor else "Medium"
    for name in priorities:
        if name in BUILTIN_LEVELS:
            current_level = name
        frappe.db.set_value(
            "HD Ticket Priority", name, "level", current_level, update_modified=False
        )
