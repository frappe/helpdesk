import frappe
from frappe.query_builder.functions import Coalesce

from helpdesk.consts import (
    NEVER_CUSTOMER_VISIBLE_FIELDS,
    SERVER_COMPUTED_FIELDS,
    TICKET_INTERNAL_FIELD_PERMLEVEL,
)


def execute():
    """Move the deleted hide_from_customer flag onto the Visible to column.

    Query builder because the flag is gone from the doctype, so the ORM cannot
    see it. Frappe never drops a removed field's column, so it is still readable.
    """
    if not frappe.db.has_column("HD Ticket Template Field", "hide_from_customer"):
        return
    TemplateField = frappe.qb.DocType("HD Ticket Template Field")
    # migrate hide_from_customers to visible_to
    (
        frappe.qb.update(TemplateField)
        .set(TemplateField.visible_to, "Agents")
        .where(TemplateField.hide_from_customer == 1)
    ).run()
    # everything rest is visible to everyone by default
    (
        frappe.qb.update(TemplateField)
        .set(TemplateField.visible_to, "Everyone")
        .where(Coalesce(TemplateField.visible_to, "") == "")
    ).run()
    hide_rows_the_template_may_not_show()


def hide_rows_the_template_may_not_show():
    """fields that maybe in hd ticket template which should be internal"""
    TemplateField = frappe.qb.DocType("HD Ticket Template Field")
    (
        frappe.qb.update(TemplateField)
        .set(TemplateField.visible_to, "Agents")
        .where(TemplateField.fieldname.isin(list(never_customer_visible_fieldnames())))
    ).run()


def never_customer_visible_fieldnames() -> set[str]:
    """The same set validate_customer_visible_fields refuses to widen."""
    internal = {
        field.fieldname
        for field in frappe.get_meta("HD Ticket").fields
        if (field.permlevel or 0) >= TICKET_INTERNAL_FIELD_PERMLEVEL
    }
    return internal | set(SERVER_COMPUTED_FIELDS) | set(NEVER_CUSTOMER_VISIBLE_FIELDS)
