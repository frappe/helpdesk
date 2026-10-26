import random
import unittest
from contextlib import contextmanager
from typing import Iterator
from unittest.mock import MagicMock, patch

import frappe
from frappe.model.document import Document
from frappe.utils import random_string

from helpdesk.integrations.whatsapp.setup import is_whatsapp_installed

# every Graph API call the whatsapp app makes goes through these
META_REQUEST = "whatsapp.whatsapp.api.whatsapp.WhatsApp._request"
META_UPLOAD = "whatsapp.whatsapp.api.whatsapp.WhatsApp.upload_media"

requires_whatsapp = unittest.skipUnless(
    is_whatsapp_installed(), "needs the whatsapp app"
)


def make_whatsapp_account(**values) -> str:
    """Insert an Active WA Account and return its name."""
    doc = frappe.get_doc(
        {
            "doctype": "WA Account",
            "account_name": f"Test {random_string(6)}",
            "phone_id": random_string(10),
            "business_id": random_string(10),
            "status": "Active",
            "access_token": "test-token",
            **values,
        }
    )
    return doc.insert(ignore_permissions=True).name


def receive_message(
    sender: str, text: str, account: str, profile_name: str = "Test Customer", **msg
) -> Document:
    """Deliver a text the way Meta's webhook does, and return the stored WA Message."""
    from whatsapp.whatsapp.webhook import _create_incoming_message

    message = {
        "from": sender,
        "id": f"wamid.{random_string(16)}",
        "type": "text",
        "text": {"body": text},
        **msg,
    }
    _create_incoming_message(message, account, {"name": profile_name})
    return frappe.get_doc("WA Message", {"message_id": message["id"]})


def press_button(sender: str, account: str, prompt: str, button_id: str) -> Document:
    """Answer an interactive message by pressing one of its buttons, as WhatsApp sends it."""
    prompt_doc = frappe.get_doc("WA Message", prompt)
    title = next(
        row.title
        for row in prompt_doc.interactive_buttons
        if row.button_id == button_id
    )
    return receive_message(
        sender,
        "",
        account,
        type="interactive",
        interactive={"button_reply": {"id": button_id, "title": title}},
        context={"id": prompt_doc.message_id},
    )


def react_to(sender: str, account: str, message_id: str, emoji: str) -> Document:
    return receive_message(
        sender,
        "",
        account,
        type="reaction",
        reaction={"emoji": emoji, "message_id": message_id},
    )


@contextmanager
def mock_meta() -> Iterator[MagicMock]:
    """Patch the Graph API so sends and number lookups never leave the test."""
    with (
        patch(META_REQUEST, side_effect=meta_response) as request,
        patch(META_UPLOAD, side_effect=lambda *args: {"id": random_string(12)}),
    ):
        yield request


def meta_response(method: str, endpoint: str, **kwargs) -> dict:
    # a fresh id per send, so replies and reactions find the right message
    if method == "POST" and endpoint.endswith("/messages"):
        return {"messages": [{"id": f"wamid.{random_string(16)}"}]}
    return {}


def make_whatsapp_template(**values) -> str:
    """Store an Approved WA Template for tickets without registering it with Meta."""
    name = f"test_{random_string(8).lower()}"
    doc = frappe.get_doc(
        {
            "doctype": "WA Template",
            "template_label": name,
            "template_name": name,
            "message": "Hello, your ticket is {{subject}}",
            "status": "Approved",
            "template_type": "Utility",
            "reference_doctype": "HD Ticket",
            "template_variables": [
                {
                    "variable_name": "subject",
                    "variable_example": "Order late",
                    "variable_field": "subject",
                }
            ],
            **values,
        }
    )
    doc.flags.from_sync = True
    return doc.insert(ignore_permissions=True).name


def make_number() -> str:
    """A random valid Indian mobile number in WhatsApp's format, without the plus."""
    return f"9198{random.randint(10**7, 10**8 - 1)}"


def sent_payloads(meta: MagicMock) -> list[dict]:
    """The message payloads posted to Meta, oldest first."""
    return [
        call.kwargs["json"]
        for call in meta.call_args_list
        if call.args[0] == "POST" and call.args[1].endswith("/messages")
    ]
