import frappe


def execute():
    """Fill visible_to on rows older than the column.
    Cosmetic: reads already fall back to hide_from_customer, so re-runs are safe."""
    frappe.db.set_value(
        "HD Ticket Template Field",
        {"visible_to": ("in", ("", None)), "hide_from_customer": 1},
        "visible_to",
        "Agents and above",
        update_modified=False,
    )
    frappe.db.set_value(
        "HD Ticket Template Field",
        {"visible_to": ("in", ("", None))},
        "visible_to",
        "Everyone",
        update_modified=False,
    )
