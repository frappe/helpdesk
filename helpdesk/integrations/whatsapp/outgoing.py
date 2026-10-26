from contextlib import contextmanager
from datetime import datetime

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_to_date, get_datetime, now_datetime

from helpdesk.integrations.whatsapp.setup import WHATSAPP_SOURCE, is_whatsapp_installed
from helpdesk.utils import is_agent

NEW_TICKET_BUTTON = "helpdesk_new_ticket"
NO_TICKET_BUTTON = "helpdesk_no_ticket"
REPLY_WINDOW_HOURS = 24
# automated sends are owned by Guest, so no agent gets credit for them
SYSTEM_SENDER = "Guest"
SLA_SAVEPOINT = "helpdesk_whatsapp_sla"


def before_insert(doc: Document, method: str | None = None) -> None:
    """Check an agent's message on a ticket and mark automated sends."""
    if doc.direction != "Outgoing":
        return
    if doc.flags.helpdesk_system_message:
        doc.owner = SYSTEM_SENDER
    elif doc.reference_doctype == "HD Ticket":
        prepare_agent_message(doc, doc.reference_docname)
    elif is_agent() and not frappe.has_permission("WA Message", "create"):
        # Helpdesk lets agents message customers on their tickets only
        frappe.throw(
            _("Reply to the customer from their ticket"), frappe.PermissionError
        )


def prepare_agent_message(doc: Document, ticket: str) -> None:
    sender = address_to_customer(doc, ticket)
    frappe.has_permission("HD Ticket", "write", ticket, throw=True)
    validate_attachment(doc, ticket)
    validate_quote(doc, ticket)
    if doc.is_template:
        validate_template_account(doc.whatsapp_template, sender.whatsapp_account)
    else:
        validate_reply_window(sender)


def address_to_customer(doc: Document, ticket: str) -> dict:
    """Send to the ticket's customer, from the Business Number they last wrote to."""
    if frappe.db.get_value("HD Ticket", ticket, "source") != WHATSAPP_SOURCE:
        frappe.throw(_("Ticket {0} is not a WhatsApp ticket").format(ticket))
    sender = get_last_incoming(ticket)
    if not sender:
        frappe.throw(_("Ticket {0} has no WhatsApp conversation").format(ticket))
    doc.to, doc.whatsapp_account = sender.to, sender.whatsapp_account
    return sender


def validate(doc: Document, method: str | None = None) -> None:
    """Lock the ticket before an agent's message reaches Meta, so stamping it afterwards never waits."""
    if is_agent_message(doc) and doc.docstatus == 1:
        lock_ticket(doc.reference_docname)


def on_submit(doc: Document, method: str | None = None) -> None:
    """Stamp the ticket's SLA once Meta accepted an agent's message; a failed stamp keeps the message Sent."""
    if doc.status != "Sent" or not is_agent_message(doc):
        return
    frappe.db.savepoint(SLA_SAVEPOINT)
    try:
        ticket = frappe.get_doc("HD Ticket", doc.reference_docname)
        ticket.record_agent_response()
        ticket.save()
    except Exception:
        frappe.db.rollback(save_point=SLA_SAVEPOINT)
        frappe.log_error(title="WhatsApp: could not record the agent's response")


def lock_ticket(ticket: str) -> None:
    frappe.db.get_value("HD Ticket", ticket, "name", for_update=True)


def is_agent_message(doc: Document) -> bool:
    return (
        doc.direction == "Outgoing"
        and doc.reference_doctype == "HD Ticket"
        and doc.reaction is None
        and doc.owner != SYSTEM_SENDER
    )


def validate_attachment(doc: Document, ticket: str) -> None:
    """Allow only this ticket's files or the agent's own fresh upload, which is then attached to the ticket."""
    if not doc.attach:
        return
    file_url = frappe.db.get_value("File", doc.attach, "file_url")
    on_ticket = {"attached_to_doctype": "HD Ticket", "attached_to_name": ticket}
    if file_url and frappe.db.exists("File", {"file_url": file_url, **on_ticket}):
        return
    upload = file_url and get_own_unattached_upload(file_url)
    if not upload:
        frappe.throw(_("Attach a file uploaded to this ticket"), frappe.PermissionError)
    frappe.db.set_value("File", upload, on_ticket)


def get_own_unattached_upload(file_url: str) -> str | None:
    return frappe.db.get_value(
        "File",
        {
            "file_url": file_url,
            "attached_to_doctype": ["is", "not set"],
            "owner": frappe.session.user,
        },
        "name",
    )


def validate_template_account(template: str | None, account: str) -> None:
    template_account = frappe.db.get_value("WA Template", template, "whatsapp_account")
    if template_account and template_account != account:
        frappe.throw(_("This template belongs to another WhatsApp number"))


def get_sendable_template_names(account: str | None) -> list[str]:
    """Approved templates a Business Number may send: its own and those tied to no number."""
    if not account:
        return []
    return frappe.get_all(
        "WA Template",
        filters={"status": "Approved"},
        or_filters=[
            ["whatsapp_account", "=", account],
            ["whatsapp_account", "is", "not set"],
        ],
        pluck="name",
    )


def validate_quote(doc: Document, ticket: str) -> None:
    quoted = {
        "message_id": doc.context_message_id,
        "reference_doctype": "HD Ticket",
        "reference_docname": ticket,
    }
    if doc.context_message_id and not frappe.db.exists("WA Message", quoted):
        frappe.throw(_("Quote a message on this ticket"), frappe.DoesNotExistError)


def validate_reply_window(last_incoming: dict | None) -> None:
    closes_at = get_reply_window_closes_at(last_incoming)
    if not closes_at or closes_at <= now_datetime():
        frappe.throw(
            _(
                "The reply window has closed. Send an approved template to restart the conversation."
            )
        )


def get_last_incoming(ticket: str) -> dict | None:
    """The customer's latest message on a ticket: their WA Profile, Business Number and time."""
    return frappe.db.get_value(
        "WA Message",
        {
            "reference_doctype": "HD Ticket",
            "reference_docname": ticket,
            "direction": "Incoming",
        },
        ["to", "whatsapp_account", "creation"],
        order_by="creation desc",
        as_dict=True,
    )


def get_reply_window_closes_at(last_incoming: dict | None) -> datetime | None:
    """When the Reply Window closes: 24 hours after the customer's last message (from get_last_incoming)."""
    if not last_incoming:
        return None
    return add_to_date(get_datetime(last_incoming.creation), hours=REPLY_WINDOW_HOURS)


def get_first_agent_reply_on(ticket: str) -> datetime | None:
    """When an agent first messaged the customer on WhatsApp; status changes and automated sends don't count."""
    if not is_whatsapp_installed():
        return None
    return frappe.db.get_value(
        "WA Message",
        {
            "reference_doctype": "HD Ticket",
            "reference_docname": ticket,
            "direction": "Outgoing",
            "docstatus": 1,
            "status": ["!=", "Failed"],
            "reaction": ["is", "not set"],
            "owner": ["!=", SYSTEM_SENDER],
        },
        "creation",
        order_by="creation asc",
    )


def send_system_message(to: str, account: str, **fields) -> None:
    """Send an automated message; if Meta refuses it, log it so the inbound message is still stored."""
    doc = frappe.get_doc(
        {
            "doctype": "WA Message",
            "direction": "Outgoing",
            "to": to,
            "whatsapp_account": account,
            **fields,
        }
    )
    doc.flags.helpdesk_system_message = True
    doc.flags.ignore_permissions = True
    try:
        doc.submit()
    except Exception:
        frappe.log_error(title="WhatsApp: could not send a system message")


def get_prompt_buttons() -> dict[str, str]:
    # Meta caps button titles at 20 characters
    return {
        NEW_TICKET_BUTTON: _("Create new ticket"),
        NO_TICKET_BUTTON: _("No, thanks"),
    }


def send_closed_ticket_prompt(to: str, account: str, closed_ticket: str) -> None:
    """Ask a customer whose last ticket is Closed whether to raise a new one."""
    send_system_message(
        to,
        account,
        reference_doctype="HD Ticket",
        reference_docname=closed_ticket,
        message=_(
            "Your previous ticket #{0} is closed. Do you want to raise a new one?"
        ).format(closed_ticket),
        interactive_buttons=[
            {"button_id": button_id, "title": title}
            for button_id, title in get_prompt_buttons().items()
        ],
    )


def send_no_ticket_acknowledgement(
    to: str, account: str, closed_ticket: str | None
) -> None:
    """Confirm to a customer who answered "No, thanks" that no ticket was raised."""
    send_system_message(
        to,
        account,
        reference_doctype="HD Ticket" if closed_ticket else None,
        reference_docname=closed_ticket,
        message=_(
            "Okay, we won't open a new ticket. Message us anytime if you need help."
        ),
    )


@contextmanager
def as_administrator():
    """Webhooks arrive as Guest; ticket intake runs as Administrator, as email intake does."""
    user = frappe.session.user
    frappe.set_user("Administrator")
    try:
        yield
    finally:
        frappe.set_user(user)
