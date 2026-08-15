"""Guards over desk form endpoints that bypass Comment permissions.

``get_docinfo``/``getdoc``/``get_activity_timeline`` read comments with
``frappe.get_all`` (permissions ignored), gated only on read access to the
reference document. Customers can read their own HD Tickets, so without
these wrappers they could pull agent-internal comments through any of the
three. Wired via ``override_whitelisted_methods``.
"""

import frappe
from frappe import _
from frappe.desk.form import activity, load
from frappe.model.document import Document

from helpdesk.utils import is_agent


@frappe.whitelist()
def getdoc(doctype: str, name: str | int):
    deny_non_agents(doctype)
    return load.getdoc(doctype, name)


@frappe.whitelist()
def get_docinfo(
    doc: Document | dict | str | None = None,
    doctype: str | None = None,
    name: str | int | None = None,
):
    deny_non_agents(doctype or doctype_of(doc))
    return load.get_docinfo(doc, doctype, name)


@frappe.whitelist()
def get_activity_timeline(doctype: str, name: str | int) -> dict:
    deny_non_agents(doctype)
    return activity.get_activity_timeline(doctype, name)


def deny_non_agents(doctype: str | None):
    if doctype == "HD Ticket" and not is_agent():
        frappe.throw(_("Not permitted"), frappe.PermissionError)


def doctype_of(doc: Document | dict | str | None) -> str | None:
    if isinstance(doc, str):
        doc = frappe.parse_json(doc)
    if isinstance(doc, dict):
        return doc.get("doctype")
    return getattr(doc, "doctype", None)
