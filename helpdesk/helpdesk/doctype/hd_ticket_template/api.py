import json

import frappe

from helpdesk.field_visibility import hidden_ticket_fields
from helpdesk.helpdesk.doctype.hd_form_script.hd_form_script import get_form_script
from helpdesk.utils import check_permissions, get_customers, is_agent

DOCTYPE_TEMPLATE = "HD Ticket Template"
DOCTYPE_TEMPLATE_FIELD = "HD Ticket Template Field"
DOCTYPE_TICKET = "HD Ticket"


@frappe.whitelist()
def get_one(name: str):
    check_permissions(DOCTYPE_TEMPLATE, None)
    found, about, description_template = frappe.get_value(
        DOCTYPE_TEMPLATE, name, ["name", "about", "description_template"]
    ) or [None, None, None]
    if not found:
        return {"about": None, "fields": []}
    fields = get_fields_meta(name)
    if frappe.db.get_single_value("HD Settings", "auto_set_customer_from_contact"):
        set_customer_field(fields)

    return {
        "about": about,
        "fields": fields,
        "description_template": description_template,
        "_form_script": get_form_script(
            "HD Ticket", apply_on_new_page=True, is_customer_portal=False
        ),
    }


def get_fields_meta(template: str):
    """The template's fields, as this user may see them."""
    hidden = hidden_ticket_fields()
    meta = frappe.get_meta(DOCTYPE_TICKET)
    fields = []
    for row in template_rows(template):
        field = meta.get_field(row.fieldname)
        if row.fieldname in hidden or not field:
            continue
        fields.append(form_field(row, field))
    return fields


def template_rows(template: str) -> list:
    return frappe.get_all(
        DOCTYPE_TEMPLATE_FIELD,
        filters={"parent": template, "parenttype": DOCTYPE_TEMPLATE},
        fields=[
            "fieldname",
            "visible_to",
            "required",
            "url_method",
            "placeholder",
            "idx",
        ],
        order_by="idx",
    )


def form_field(row, field) -> frappe._dict:
    """One field for the form: the template's own columns, plus live doctype meta.

    Meta is cached and already carries Customize Form overrides, so nothing here
    reads DocField or Property Setter directly.
    """
    return frappe._dict(
        fieldname=row.fieldname,
        visible_to=row.visible_to,
        required=row.required,
        url_method=row.url_method,
        placeholder=row.placeholder,
        idx=row.idx,
        label=field.label,
        fieldtype=field.fieldtype,
        options=field.options,
        link_filters=field.link_filters,
        depends_on=field.depends_on,
        mandatory_depends_on=field.mandatory_depends_on,
        read_only_depends_on=field.read_only_depends_on,
    )


def set_customer_field(fields: list) -> None:
    """Scope the customer field to the session contact's own customers on the
    customer portal.

    Agents get the template's customer field untouched. Portal contacts get it
    filtered to their customers; when the template has no customer field and the
    contact belongs to multiple customers, a required field is injected so they
    can pick one. Selection is enforced server side in HDTicket.set_customer.
    """
    if is_agent():
        return

    customers = get_customers()
    link_filters = json.dumps([["HD Customer", "name", "in", list(customers)]])
    customer_field = next((f for f in fields if f.fieldname == "customer"), None)

    if customer_field:
        customer_field.link_filters = link_filters
        if len(customers) > 1:
            customer_field.required = 1
            customer_field.visible_to = "Everyone"
    elif len(customers) > 1:
        fields.append(
            frappe._dict(
                fieldname="customer",
                fieldtype="Link",
                label="Customer",
                options="HD Customer",
                link_filters=link_filters,
                required=1,
                idx=len(fields) + 1,
            )
        )
