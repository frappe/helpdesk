import json

import frappe

from helpdesk.helpdesk.doctype.hd_form_script.hd_form_script import get_form_script
from helpdesk.ticket_fields import TicketFields
from helpdesk.utils import check_permissions, get_customers, is_agent

DOCTYPE_TEMPLATE = "HD Ticket Template"


@frappe.whitelist()
def get_one(name: str):
    check_permissions(DOCTYPE_TEMPLATE, None)
    found, about, description_template = frappe.get_value(
        DOCTYPE_TEMPLATE, name, ["name", "about", "description_template"]
    ) or [None, None, None]
    if not found:
        return {"about": None, "fields": []}
    fields = TicketFields().form
    if frappe.db.get_single_value("HD Settings", "auto_set_customer_from_contact"):
        set_customer_field(fields)

    return {
        "about": about,
        "fields": fields,
        "description_template": description_template,
        "_form_script": get_form_script(
            "HD Ticket", apply_on_new_page=True, is_customer_portal=not is_agent()
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
    elif len(customers) > 1:
        fields.append(
            frappe._dict(
                fieldname="customer",
                fieldtype="Link",
                label="Customer",
                options="HD Customer",
                link_filters=link_filters,
                required=1,
            )
        )
