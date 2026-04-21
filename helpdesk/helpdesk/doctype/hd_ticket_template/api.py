import json
from typing import Literal

import frappe
from pypika import JoinType

from helpdesk.helpdesk.doctype.hd_form_script.hd_form_script import get_form_script
from helpdesk.utils import check_permissions, get_customers

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
    # fields = [field for field in fields if field.fieldname != "customer"]

    customers = (
        json.dumps(get_customers()) if get_customers() else "[]"
    )  # required format of link_filters
    # if (len(customers)) > 1:
    # customer_field = {
    #     "fieldname": "customer",
    #     "fieldtype": "Link",
    #     "label": "Customer",
    #     "options": "HD Customer",
    #     "required": 1,
    #     "link_filters": '[["HD Customer","name","in",' + customers + "]]",
    # }
    #     fields.insert(0, customer_field)

    return {
        "about": about,
        "fields": fields,
        "description_template": description_template,
        "_form_script": get_form_script(
            "HD Ticket", apply_on_new_page=True, is_customer_portal=False
        ),
        "customers": customers,
    }


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
    return result
    return result
    return result
    return result
    return result
    return result
    return result
