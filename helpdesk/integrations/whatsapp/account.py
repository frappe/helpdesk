import frappe
from frappe import _
from frappe.model.document import Document

TICKET_DOCTYPE = "HD Ticket"


def validate(doc: Document, method: str | None = None) -> None:
    """Refuse an append action to HD Ticket: it files the message held while a customer answers the closed-ticket prompt on the closed ticket."""
    for action in doc.get("append_actions", []):
        if action.append_to == TICKET_DOCTYPE:
            frappe.throw(
                _(
                    "Row #{0}: Helpdesk files WhatsApp messages on tickets itself, so remove this append action to HD Ticket."
                ).format(action.idx),
                title=_("Append action not allowed"),
            )
