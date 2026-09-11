import frappe

from helpdesk.field_visibility import fields_visible_to


def execute():
    """Move the deleted hide_from_customer flag onto the Visible to column.

    Raw SQL because the flag is gone from the doctype, so the ORM cannot see it.
    Frappe never drops a removed field's column, so it is still readable here.
    """
    if not frappe.db.has_column("HD Ticket Template Field", "hide_from_customer"):
        return
    # keyed off the flag, never off a blank visible_to: schema sync fills every
    # existing row with the column default before this patch runs
    frappe.db.sql(
        "update `tabHD Ticket Template Field`"
        " set visible_to = 'Agents' where hide_from_customer = 1"
    )
    frappe.db.sql(
        "update `tabHD Ticket Template Field`"
        " set visible_to = 'Everyone' where coalesce(visible_to, '') = ''"
    )
    # migrate clears the cache before patches run, not after
    fields_visible_to.clear_cache()
