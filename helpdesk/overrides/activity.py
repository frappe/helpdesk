import frappe
from frappe import _
from frappe.desk.form import activity, load

from helpdesk.utils import is_agent

# Who else an email went to; a customer never sees it, so the response must not carry it.
RECIPIENT_FIELDS = ("to", "cc", "bcc")


@frappe.whitelist()
def get_activity_timeline(
    doctype: str,
    name: str | int,
    visible_types: list[str | dict[str, list[str]]] | str | None = None,
) -> dict:
    result = activity.get_activity_timeline(doctype, name, visible_types)
    return strip_recipients(doctype, result)


@frappe.whitelist()
def get_more_email_activities(doctype: str, name: str | int, start: int) -> dict:
    result = activity.get_more_email_activities(doctype, name, start)
    return strip_recipients(doctype, result)


def strip_recipients(doctype: str, result: dict) -> dict:
    if doctype != "HD Ticket" or is_agent():
        return result
    for row in result["activities"]:
        if row["type"] == "email":
            for field in RECIPIENT_FIELDS:
                row["data"].pop(field, None)
    return result


# The desk form loaders send docinfo (recipients, assignments, versions); customers have no desk form.
@frappe.whitelist()
def getdoc(doctype: str, name: str | int):
    deny_ticket_form_to_customers(doctype)
    return load.getdoc(doctype, name)


@frappe.whitelist()
def get_docinfo(
    doc: str | dict | None = None,
    doctype: str | None = None,
    name: str | int | None = None,
):
    if isinstance(doc, dict):
        doctype = doctype or doc.get("doctype")
    deny_ticket_form_to_customers(doctype)
    return load.get_docinfo(doc, doctype, name)


@frappe.whitelist()
def get_communications(
    doctype: str, name: str | int, start: str | int = 0, limit: str | int = 20
):
    deny_ticket_form_to_customers(doctype)
    return load.get_communications(doctype, name, start, limit)


def deny_ticket_form_to_customers(doctype: str | None) -> None:
    if doctype == "HD Ticket" and not is_agent():
        frappe.throw(_("Not permitted"), frappe.PermissionError)
