import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.query_builder import Order
from frappe.utils import escape_html, now_datetime

from helpdesk.helpdesk.doctype.hd_ticket.hd_ticket import ping_customers
from helpdesk.integrations.whatsapp.outgoing import (
    NEW_TICKET_BUTTON,
    NO_TICKET_BUTTON,
    as_administrator,
    send_closed_ticket_prompt,
    send_no_ticket_acknowledgement,
)
from helpdesk.integrations.whatsapp.setup import WHATSAPP_SOURCE, is_whatsapp_installed
from helpdesk.utils import get_contact_by_international_number

SUBJECT_LENGTH = 140


def before_insert(doc: Document, method: str | None = None) -> None:
    """File an inbound message from WhatsApp onto its sender's ticket, before the app's append actions run."""
    if doc.direction == "Incoming":
        with as_administrator():
            IncomingMessage(doc).route()
    if doc.reference_doctype == "HD Ticket":
        doc.flags.helpdesk_ticket = doc.reference_docname


def before_submit(doc: Document, method: str | None = None) -> None:
    """Keep a message on its ticket when another app's validate re-links it, as CRM's does."""
    ticket = doc.flags.helpdesk_ticket
    if ticket and doc.reference_doctype != "HD Ticket":
        doc.reference_doctype, doc.reference_docname = "HD Ticket", ticket


def after_insert(doc: Document, method: str | None = None) -> None:
    """Customers aren't in the ticket's room, so ping their portal on every new message."""
    if doc.reference_doctype != "HD Ticket" or not doc.reference_docname:
        return
    ticket = frappe.db.get_value(
        "HD Ticket",
        doc.reference_docname,
        ["name", "raised_by", "owner", "contact", "customer"],
        as_dict=True,
    )
    if ticket:
        ping_customers(ticket)


def after_status_log(log: Document, method: str | None = None) -> None:
    """Ping the portal when a sent message turns Failed, the one status change it shows."""
    # ponytail: the app's status update only writes a WA Log; hook WA Message once it runs a doc event
    if log.event_type != "Webhook" or log.reference_doctype != "WA Message":
        return
    message = frappe.db.get_value(
        "WA Message",
        log.reference_docname,
        ["status", "reference_doctype", "reference_docname"],
        as_dict=True,
    )
    if message and message.status == "Failed":
        after_insert(message)


def delete_thread(doc: Document, method: str | None = None) -> None:
    """Delete a ticket's WhatsApp messages with it, so a ticket reusing its name starts empty."""
    if is_whatsapp_installed():
        frappe.db.delete(
            "WA Message",
            {"reference_doctype": "HD Ticket", "reference_docname": doc.name},
        )


class IncomingMessage:
    """One inbound message, routed by the sender's Active WhatsApp Ticket.

    The webhook holds the sender's WA Profile row locked, so reads here lock
    too: a locking read sees what the sender's previous delivery committed.
    """

    def __init__(self, message: Document):
        self.message = message
        self.profile = message.to
        self.account = message.whatsapp_account

    def route(self) -> None:
        """Link the message to the sender's ticket on this Business Number, or ask first."""
        if self.message.reaction is not None:
            return self.link_to_reacted_message()
        ticket = self.get_last_ticket()
        answer = self.get_prompt_answer()
        if answer:
            return self.answer_prompt(answer, ticket)
        if not ticket:
            return self.open_ticket([])
        if ticket.status != "Closed":
            return self.add_to(ticket)
        if not self.is_prompt_pending(ticket.name):
            send_closed_ticket_prompt(self.profile, self.account, ticket.name)

    def link_to_reacted_message(self) -> None:
        # a reaction never reopens a ticket, it only shows on the bubble
        self.message.reference_doctype, self.message.reference_docname = (
            frappe.db.get_value(
                "WA Message",
                {"message_id": self.message.context_message_id},
                ["reference_doctype", "reference_docname"],
            )
            or (None, None)
        )

    def get_last_ticket(self) -> Document | None:
        Message = frappe.qb.DocType("WA Message")
        names = (
            frappe.qb.from_(Message)
            .select(Message.reference_docname)
            .where(
                (Message.to == self.profile)
                & (Message.direction == "Incoming")
                & Message.reaction.isnull()
                & (Message.reference_doctype == "HD Ticket")
                & Message.reference_docname.isnotnull()
            )
            .orderby(Message.creation, order=Order.desc)
            .limit(1)
            .for_update()
            .run(pluck=True)
        )
        if not names or not frappe.db.exists("HD Ticket", names[0]):
            return None
        ticket = frappe.get_doc("HD Ticket", names[0], for_update=True)
        if not ticket.is_merged:
            return ticket
        target = ticket.get_merge_target()
        return frappe.get_doc("HD Ticket", target, for_update=True) if target else None

    def get_prompt_answer(self) -> str | None:
        """The button pressed, when this message answers a Closed-Ticket Prompt."""
        context = self.message.context_message_id
        prompt = context and frappe.db.get_value(
            "WA Message", {"message_id": context, "direction": "Outgoing"}
        )
        if not prompt:
            return None
        # the webhook stores the button's title, so match it on the prompt's rows
        return frappe.db.get_value(
            "WA Message Interactive Button",
            {
                "parent": prompt,
                "parenttype": "WA Message",
                "title": self.message.message,
                "button_id": ["in", [NEW_TICKET_BUTTON, NO_TICKET_BUTTON]],
            },
            "button_id",
        )

    def answer_prompt(self, answer: str, ticket: Document | None) -> None:
        if ticket and ticket.status != "Closed":
            return self.add_to(ticket)
        if answer == NEW_TICKET_BUTTON:
            held = self.get_held_messages(ticket.name) if ticket else []
            return self.open_ticket(held, answered=True)
        if ticket:
            self.link(ticket.name)
        send_no_ticket_acknowledgement(
            self.profile, self.account, ticket.name if ticket else None
        )

    def is_prompt_pending(self, closed_ticket: str) -> bool:
        # an answer to the prompt is linked to the ticket, so it ends the prompt even if the reply to it failed
        last_message = frappe.db.get_value(
            "WA Message",
            {
                "reference_doctype": "HD Ticket",
                "reference_docname": closed_ticket,
                "reaction": ["is", "not set"],
            },
            "name",
            order_by="creation desc",
            for_update=True,
        )
        return bool(last_message and is_prompt(last_message))

    def get_held_messages(self, ticket: str) -> list[dict]:
        """Messages held by the ticket's latest prompt: off any ticket, since it last heard or said anything."""
        held_since = self.get_held_since(ticket)
        if not held_since:
            return []
        Message = frappe.qb.DocType("WA Message")
        return (
            frappe.qb.from_(Message)
            .select(Message.name, Message.message, Message.media_id)
            .where(
                (Message.to == self.profile)
                & (Message.direction == "Incoming")
                & Message.reaction.isnull()
                # another app (CRM) may have linked it to its own record
                & (
                    Message.reference_doctype.isnull()
                    | (Message.reference_doctype != "HD Ticket")
                )
                & (Message.creation > held_since)
            )
            .orderby(Message.creation)
            .for_update()
            .run(as_dict=True)
        )

    def get_held_since(self, closed_ticket: str) -> str | None:
        # the message that triggered the prompt came in just before it, so look past the prompt
        prompts = frappe.get_all(
            "WA Message",
            filters=[
                ["WA Message", "direction", "=", "Outgoing"],
                ["WA Message", "to", "=", self.profile],
                ["WA Message", "reference_docname", "=", closed_ticket],
                ["WA Message Interactive Button", "button_id", "=", NEW_TICKET_BUTTON],
            ],
            pluck="creation",
            order_by="creation desc",
            limit=1,
        )
        if not prompts:
            return None
        return frappe.db.get_value(
            "WA Message",
            {
                "reference_doctype": "HD Ticket",
                "reference_docname": closed_ticket,
                "reaction": ["is", "not set"],
                "creation": ["<", prompts[0]],
            },
            "creation",
            order_by="creation desc",
        )

    def open_ticket(self, held: list[dict], answered: bool = False) -> None:
        # a button answer is not part of the customer's problem
        messages = held if answered else [*held, self.message]
        texts = [m.message for m in messages if m.message and not m.media_id]
        contact = self.get_or_create_contact()
        ticket = frappe.get_doc(
            {
                "doctype": "HD Ticket",
                "subject": self.get_subject(texts, contact),
                "description": "<br>".join(to_html(text) for text in texts),
                "contact": contact,
                "raised_by": frappe.db.get_value("Contact", contact, "email_id"),
                "source": WHATSAPP_SOURCE,
                "last_customer_response": now_datetime(),
            }
        )
        # like email intake, a field made mandatory for agents never drops a customer's message
        ticket.flags.ignore_mandatory = True
        ticket.insert(ignore_permissions=True)
        link_messages([message.name for message in held], ticket.name)
        self.link(ticket.name)

    def get_subject(self, texts: list[str], contact: str) -> str:
        if texts:
            return shorten(texts[0], SUBJECT_LENGTH)
        name = frappe.db.get_value("Contact", contact, "full_name")
        return _("Message on WhatsApp from {0}").format(name)

    def get_or_create_contact(self) -> str:
        phone, profile_name = frappe.db.get_value(
            "WA Profile", self.profile, ["phone_number", "profile_name"]
        )
        existing = get_contact_by_international_number(phone)
        if existing:
            return existing
        contact = frappe.new_doc("Contact")
        # Contact names reject angle brackets, which would drop every message from this sender
        contact.first_name = re.sub(r"[<>]", "", profile_name or "").strip() or phone
        contact.add_phone(phone, is_primary_mobile_no=1)
        return contact.insert(ignore_permissions=True).name

    def add_to(self, ticket: Document) -> None:
        ticket.last_customer_response = now_datetime()
        if ticket.status_category in ("Paused", "Resolved"):
            ticket.status = ticket.ticket_reopen_status
            # like an inbound email, the reopen notification names the customer when they have a login
            ticket.flags.reopened_by = frappe.db.get_value(
                "Contact", ticket.contact, "user"
            )
        ticket.flags.ignore_mandatory = True
        ticket.save(ignore_permissions=True)
        self.link(ticket.name)
        # an agent may have reopened the ticket while a Closed-Ticket Prompt held messages
        link_messages(
            [message.name for message in self.get_held_messages(ticket.name)],
            ticket.name,
        )

    def link(self, ticket: str) -> None:
        self.message.reference_doctype = "HD Ticket"
        self.message.reference_docname = ticket


def is_prompt(message: str) -> bool:
    return bool(
        frappe.db.exists(
            "WA Message Interactive Button",
            {
                "parent": message,
                "parenttype": "WA Message",
                "button_id": NEW_TICKET_BUTTON,
            },
        )
    )


def shorten(text: str, length: int) -> str:
    """One line of at most `length` characters, cut mid-word if it must be."""
    text = " ".join(text.split())
    return text if len(text) <= length else text[: length - 1] + "…"


def to_html(text: str) -> str:
    return escape_html(text).replace("\n", "<br>")


def link_messages(names: list[str], ticket: str) -> None:
    if not names:
        return
    Message = frappe.qb.DocType("WA Message")
    frappe.qb.update(Message).set(Message.reference_doctype, "HD Ticket").set(
        Message.reference_docname, ticket
    ).where(Message.name.isin(names)).run()
