from typing import Literal

import frappe
from frappe.desk.reportview import delete_bulk


@frappe.whitelist(methods=["GET"])
def search_contacts(
    txt: str,
) -> list[dict[Literal["full_name", "name", "email_id"], str]]:
    doctype = "Contact"
    or_filters: list[list[str]] = []
    search_fields = ["full_name", "email_id", "name"]
    if txt:
        for field in search_fields:
            or_filters.append([doctype, field, "like", f"%{txt}%"])
    return frappe.get_list(
        doctype,
        filters=[[doctype, "email_id", "is", "set"]],
        fields=search_fields,
        or_filters=or_filters,
        limit_start=0,
        limit_page_length=10,
        order_by="email_id, full_name, name",
        ignore_permissions=False,
        strict=False,
    )


@frappe.whitelist()
def delete_contact(name: str):
    frappe.has_permission("Contact", "delete", throw=True)
    tickets = frappe.get_list("HD Ticket", filters={"contact": name}, pluck="name")
    delete_bulk("HD Ticket", tickets)
    customers = frappe.get_all(
        "HD Customer Member",
        filters={"contact_name": name},
        pluck="parent",
    )
    delete_bulk("HD Customer Member", customers)
    frappe.delete_doc("Contact", name)
