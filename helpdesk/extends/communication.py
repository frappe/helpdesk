import frappe
from frappe import _
from frappe.core.doctype.communication import email
from frappe.model.document import Document

from helpdesk.integrations.whatsapp.setup import WHATSAPP_SOURCE


@frappe.whitelist()
def make(**kwargs) -> dict:
    """The framework's email endpoint, refused for a WhatsApp ticket whatever the caller sets."""
    if kwargs.get("doctype") == "HD Ticket":
        refuse_whatsapp_ticket(kwargs.get("name"))
    return frappe.call(email.make, **kwargs)


def before_insert(doc: Document, method: str | None = None) -> None:
    """A WhatsApp ticket has no email thread, so only a Notification rule's email may land on it."""
    if doc.reference_doctype == "HD Ticket" and not is_notification(doc):
        refuse_whatsapp_ticket(doc.reference_name)


def refuse_whatsapp_ticket(ticket: str | None) -> None:
    if is_whatsapp_ticket(ticket):
        frappe.throw(_("Reply to this ticket on WhatsApp."))


def is_whatsapp_ticket(ticket: str | None) -> bool:
    return frappe.db.get_value("HD Ticket", ticket, "source") == WHATSAPP_SOURCE


def is_notification(doc: Document) -> bool:
    # caller controlled, so `make` above refuses it; Notification rules call _make
    return (
        doc.communication_type == "Automated Message" and doc.sent_or_received == "Sent"
    )
