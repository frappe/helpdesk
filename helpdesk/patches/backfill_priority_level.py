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

    # Lower integer_value = higher priority, so ascending walks most urgent
    # first. integer_value was never mandatory: null-valued customs sort last
    # (else they'd lead the walk and wrongly inherit Urgent).
    priorities = frappe.get_all("HD Ticket Priority", fields=["name", "integer_value"])
    priorities.sort(key=lambda p: (p.integer_value is None, p.integer_value or 0))

    has_anchor = any(p.name in BUILTIN_LEVELS for p in priorities)
    current_level = "Urgent" if has_anchor else "Medium"
    for priority in priorities:
        if priority.name in BUILTIN_LEVELS:
            current_level = priority.name
        frappe.db.set_value(
            "HD Ticket Priority",
            priority.name,
            "level",
            current_level,
            update_modified=False,
        )
