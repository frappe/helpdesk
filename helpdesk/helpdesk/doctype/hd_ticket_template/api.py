import json
from typing import Literal

import frappe
from pypika import JoinType

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
            customer_field.hide_from_customer = 0
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


def get_fields_meta(template: str):
    fields = get_fields(template, "DocField")
    fields.extend(get_fields(template, "Custom Field"))
    fields = sorted(fields, key=lambda x: x.idx)
    return fields


def get_fields(template: str, fetch: Literal["Custom Field", "DocField"]):
    QBField = frappe.qb.DocType(DOCTYPE_TEMPLATE_FIELD)
    QBFetch = frappe.qb.DocType(fetch)
    fields = (
        frappe.qb.from_(QBField)
        .select(QBField.star)
        .where(QBField.parent == template)
        .where(QBField.parentfield == "fields")
        .where(QBField.parenttype == DOCTYPE_TEMPLATE)
    )
    where_parent = QBFetch.parent == DOCTYPE_TICKET
    if fetch == "Custom Field":
        where_parent = QBFetch.dt == DOCTYPE_TICKET
    result = (
        frappe.qb.from_(fields)
        .select(
            QBFetch.description,
            QBFetch.fieldtype,
            QBFetch.label,
            QBFetch.options,
            QBFetch.link_filters,
            QBFetch.depends_on,
            QBFetch.mandatory_depends_on,
            fields.fieldname,
            fields.hide_from_customer,
            fields.required,
            fields.url_method,
            fields.placeholder,
            fields.idx,
        )
        .join(QBFetch, JoinType.inner)
        .on(QBFetch.fieldname == fields.fieldname)
        .where(where_parent)
        .orderby(fields.idx)
        .run(as_dict=True)
    )
    docfields = ["link_filters", "depends_on", "mandatory_depends_on"]

    for df in docfields:
        for field in result:
            property_setter_id = "HD Ticket" + "-" + field.fieldname + "-" + df
            if frappe.db.exists("Property Setter", property_setter_id):
                field[df] = frappe.get_value(
                    "Property Setter", property_setter_id, "value"
                )
    return result
