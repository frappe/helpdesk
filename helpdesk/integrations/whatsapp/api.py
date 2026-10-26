import json

import frappe
from frappe.utils import now_datetime

from helpdesk.api.saved_replies import get_rendered_saved_reply
from helpdesk.integrations.whatsapp.business_number import get_business_number
from helpdesk.integrations.whatsapp.formatting import html_to_whatsapp
from helpdesk.integrations.whatsapp.outgoing import (
    get_last_incoming,
    get_reply_window_closes_at,
    get_sendable_template_names,
)
from helpdesk.integrations.whatsapp.setup import is_whatsapp_installed
from helpdesk.utils import agent_only

# What the portal renders; send errors, numbers and ids stay with agents.
PORTAL_FIELDS = (
    "name",
    "direction",
    "creation",
    "message",
    "mime_type",
    "media_url",
    "file_name",
    "is_template",
    "template",
    "header",
    "footer",
    "buttons",
    "reply_to",
    "reply_message",
    "reactions",
    "status",
)


@frappe.whitelist()
def get_conversation(ticket: str) -> dict:
    """Who to answer on a ticket, whether the Reply Window is open and which templates may go, for the agent's composer."""
    frappe.has_permission("HD Ticket", "read", ticket, throw=True)
    if not is_whatsapp_installed():
        return {
            "installed": False,
            "to": None,
            "reply_window_open": False,
            "reply_window_closes_at": None,
            "business_number": None,
            "templates": [],
        }
    last_incoming = get_last_incoming(ticket)
    sender = last_incoming or {}
    closes_at = get_reply_window_closes_at(last_incoming)
    return {
        "installed": True,
        "to": sender.get("to"),
        "reply_window_open": bool(closes_at and closes_at > now_datetime()),
        "reply_window_closes_at": closes_at,
        "business_number": get_business_number(last_incoming),
        "templates": get_sendable_template_names(sender.get("whatsapp_account")),
    }


@frappe.whitelist()
def get_messages(ticket: str) -> dict:
    """A ticket's WhatsApp thread for the read-only portal; empty when the whatsapp app is not installed."""
    frappe.has_permission("HD Ticket", "read", ticket, throw=True)
    if not is_whatsapp_installed():
        return {
            "installed": False,
            "messages": [],
            "reply_window_open": False,
            "business_number": None,
        }
    from whatsapp.whatsapp.api.messages import get_messages as get_thread

    last_incoming = get_last_incoming(ticket)
    closes_at = get_reply_window_closes_at(last_incoming)
    return {
        "installed": True,
        "messages": [
            to_portal_row(message)
            for message in add_prompt_buttons(
                get_thread(json.dumps([["HD Ticket", ticket]]))
            )
        ],
        "reply_window_open": bool(closes_at and closes_at > now_datetime()),
        "business_number": get_business_number(last_incoming),
    }


@frappe.whitelist()
@agent_only
def render_saved_reply(ticket: str, saved_reply: str) -> str:
    """A saved reply rendered for the ticket, as WhatsApp formatted text."""
    return html_to_whatsapp(get_rendered_saved_reply(ticket, saved_reply)["message"])


def to_portal_row(message: dict) -> frappe._dict:
    """Keep only what the portal renders; an incoming media_url is the sender's file name, not a site File."""
    row = frappe._dict(
        {field: message[field] for field in PORTAL_FIELDS if field in message}
    )
    if row.buttons:
        row.buttons = [
            {"button_text": button["button_text"], "button_type": button["button_type"]}
            for button in row.buttons
        ]
    if row.direction == "Incoming":
        row.pop("file_name", None)
    return row


def add_prompt_buttons(messages: list[dict]) -> list[dict]:
    """Show a prompt's reply buttons the way the portal shows a template's."""
    rows = frappe.get_all(
        "WA Message Interactive Button",
        filters={
            "parenttype": "WA Message",
            "parent": ["in", [message["name"] for message in messages] or [""]],
        },
        fields=["parent", "title"],
        order_by="idx asc",
    )
    for message in messages:
        buttons = [
            {"button_text": row.title, "button_type": "QUICK_REPLY"}
            for row in rows
            if row.parent == message["name"]
        ]
        if buttons:
            message["buttons"] = buttons
    return messages
