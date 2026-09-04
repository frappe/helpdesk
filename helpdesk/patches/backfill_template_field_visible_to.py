import frappe


def execute():
    """Fill the visible_to tier on template rows that predate the column, so
    the grid shows the truth from day one. Reads already fall back to the
    hide_from_customer flag, so this is cosmetic and safe to re-run."""
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
