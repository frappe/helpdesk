import frappe

FIELD = "confirm_resolution_after_days"


def execute():
    """A Single skips a new field's default on upgrade, and its next save would store 0."""
    if FIELD in frappe.db.get_singles_dict("HD Settings"):
        return
    default = frappe.get_meta("HD Settings").get_field(FIELD).default
    frappe.db.set_single_value("HD Settings", FIELD, default)
