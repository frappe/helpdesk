import frappe


def execute():
    """Backfill customer_type for existing customers created before the field existed."""
    frappe.db.set_value(
        "HD Customer",
        {"customer_type": ["in", ["", None]]},
        "customer_type",
        "Company",
        update_modified=False,
    )
