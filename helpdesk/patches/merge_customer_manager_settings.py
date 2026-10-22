import frappe
from frappe.utils import cint

OLD_FIELDS = [
    "allow_customer_managers_to_manage_members",
    "allow_customer_managers_to_edit_organization",
]


def execute():
    """Fold the two customer manager switches into one. It takes the member
    management value: the logo switch alone must not let managers remove members."""
    singles = frappe.qb.DocType("Singles")
    allowed = (
        frappe.qb.from_(singles)
        .select(singles.value)
        .where((singles.doctype == "HD Settings") & (singles.field == OLD_FIELDS[0]))
        .run(pluck=True)
    )
    frappe.db.set_single_value(
        "HD Settings",
        "allow_customer_managers_to_manage_organization",
        cint(allowed[0] if allowed else 0),
    )
    frappe.db.delete("Singles", {"doctype": "HD Settings", "field": ["in", OLD_FIELDS]})
