import frappe
from frappe.desk.form import activity

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
