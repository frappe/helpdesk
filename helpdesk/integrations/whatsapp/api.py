"""Whitelisted API for the WhatsApp conversation, keyed on ``Contact``.

The frontend (Contact page and ticket) calls these to read a contact's thread
and to send text, media, templates and reactions. Every method is gated to
agents and to permission on the anchored Contact. Ported from Frappe CRM's
``crm.api.whatsapp`` to Helpdesk's Contact-anchored, omnichannel model.
"""

import json

import frappe
from frappe import _

from helpdesk.integrations.whatsapp.utils import (
    assert_ticket_belongs_to_contact,
    counterparty_number,
    get_contact_whatsapp_number,
)
from helpdesk.integrations.whatsapp.utils import (
    is_whatsapp_enabled as _is_whatsapp_enabled,
)
from helpdesk.integrations.whatsapp.utils import (
    is_whatsapp_installed as _is_whatsapp_installed,
)
from helpdesk.integrations.whatsapp.utils import validate_whatsapp_access

MESSAGE_FIELDS = [
    "name",
    "type",
    "to",
    "from",
    "content_type",
    "message_type",
    "attach",
    "template",
    "use_template",
    "message_id",
    "is_reply",
    "reply_to_message_id",
    "creation",
    "message",
    "status",
    "reference_doctype",
    "reference_name",
    "template_parameters",
    "template_header_parameters",
]


# ── Public API ────────────────────────────────────────────────────────────


@frappe.whitelist()
def is_whatsapp_installed() -> bool:
    return _is_whatsapp_installed()


@frappe.whitelist()
def is_whatsapp_enabled() -> bool:
    return _is_whatsapp_enabled()


@frappe.whitelist()
def get_whatsapp_messages(contact: str) -> list[dict]:
    """Return the WhatsApp thread anchored on ``contact``.

    Enriches template messages with their rendered body, attaches reactions to
    the messages they react to, and resolves reply-to context — mirroring the
    CRM's presentation so the shared frontend components port unchanged.
    """
    validate_whatsapp_access("Contact", contact)

    if not _is_whatsapp_installed():
        return []

    fields = list(MESSAGE_FIELDS)
    if frappe.db.has_column("WhatsApp Message", "hd_ticket"):
        fields.append("hd_ticket")

    messages = frappe.get_all(
        "WhatsApp Message",
        filters={"reference_doctype": "Contact", "reference_name": contact},
        fields=fields,
        order_by="creation asc",
    )

    _enrich_templates(messages)
    _attach_reactions(messages)
    _set_from_names(contact, messages)
    _resolve_replies(messages)

    return [m for m in messages if m["content_type"] != "reaction"]


@frappe.whitelist()
def create_whatsapp_message(
    contact: str,
    message: str,
    attach: str | None = None,
    reply_to: str | None = None,
    content_type: str = "text",
    hd_ticket: str | None = None,
) -> str:
    """Send a text/media/reaction message to ``contact`` over WhatsApp.

    :param contact: The Contact this conversation is anchored on.
    :param message: Message body (falls back to ``attach`` for media-only).
    :param attach: File URL for a media message.
    :param reply_to: ``WhatsApp Message`` name being replied to.
    :param content_type: ``text``, ``image``, ``document``, ``reaction``, ...
    :param hd_ticket: Optional ticket to record the message was sent from.
    :return: The created ``WhatsApp Message`` name.
    """
    validate_whatsapp_access("Contact", contact)
    to = _resolve_destination(contact)
    assert_ticket_belongs_to_contact(hd_ticket, contact)
    doc = frappe.new_doc("WhatsApp Message")

    if reply_to:
        reply_doc = _get_reply_doc(reply_to)
        _assert_same_conversation(reply_doc, contact)
        doc.update({"is_reply": True, "reply_to_message_id": reply_doc.message_id})

    doc.update(
        {
            "reference_doctype": "Contact",
            "reference_name": contact,
            "message": message or attach,
            "to": to,
            "attach": attach,
            "content_type": content_type,
        }
    )
    if hd_ticket and frappe.db.has_column("WhatsApp Message", "hd_ticket"):
        doc.hd_ticket = hd_ticket
    doc.insert(ignore_permissions=True)
    return doc.name


@frappe.whitelist()
def send_whatsapp_template(
    contact: str, template: str, hd_ticket: str | None = None
) -> str:
    """Send a pre-approved WhatsApp template message to ``contact``."""
    validate_whatsapp_access("Contact", contact)
    to = _resolve_destination(contact)
    assert_ticket_belongs_to_contact(hd_ticket, contact)
    doc = frappe.new_doc("WhatsApp Message")
    doc.update(
        {
            "reference_doctype": "Contact",
            "reference_name": contact,
            "message_type": "Template",
            "message": "Template message",
            "content_type": "text",
            "use_template": True,
            "template": template,
            "to": to,
        }
    )
    if hd_ticket and frappe.db.has_column("WhatsApp Message", "hd_ticket"):
        doc.hd_ticket = hd_ticket
    doc.insert(ignore_permissions=True)
    return doc.name


@frappe.whitelist()
def react_on_whatsapp_message(emoji: str, reply_to: str) -> str:
    """React with ``emoji`` to the message named ``reply_to``.

    The reaction inherits the target's anchor and is addressed to the same
    counterparty number the target used, so a reaction always lands in the
    right conversation.
    """
    target = _get_reply_doc(reply_to)
    validate_whatsapp_access(target.reference_doctype, target.reference_name)

    doc = frappe.new_doc("WhatsApp Message")
    doc.update(
        {
            "reference_doctype": target.reference_doctype,
            "reference_name": target.reference_name,
            "message": emoji,
            "to": counterparty_number(target),
            "reply_to_message_id": target.message_id,
            "content_type": "reaction",
        }
    )
    doc.insert(ignore_permissions=True)
    return doc.name


# ── Internal helpers ──────────────────────────────────────────────────────


def _resolve_destination(contact: str) -> str:
    """The number to send to — the one the customer is reachable at.

    Prefers the sender of the most recent inbound message, which is the number
    actually in use on this conversation (and may be a secondary number of the
    contact); falls back to the contact's primary number when the agent opens
    the conversation. Never a client-supplied value, so the endpoint can't be
    used as a gateway to an arbitrary destination.
    """
    last_inbound = frappe.db.get_value(
        "WhatsApp Message",
        {
            "reference_doctype": "Contact",
            "reference_name": contact,
            "type": "Incoming",
        },
        "from",
        order_by="creation desc",
    )
    to = last_inbound or get_contact_whatsapp_number(contact)
    if not to:
        frappe.throw(
            _("Contact {0} has no WhatsApp number.").format(contact),
            frappe.ValidationError,
        )
    return to


def _get_reply_doc(name: str) -> "frappe.Document":
    if not frappe.db.exists("WhatsApp Message", name):
        frappe.throw(
            _("Referenced WhatsApp message does not exist."), frappe.DoesNotExistError
        )
    doc = frappe.get_doc("WhatsApp Message", name)
    if not doc.has_permission("read"):
        frappe.throw(
            _("Not permitted to access the referenced WhatsApp message."),
            frappe.PermissionError,
        )
    return doc


def _assert_same_conversation(reply_doc, contact: str) -> None:
    """Reject replying across conversations.

    Agents hold global read on ``WhatsApp Message``, so a read check alone would
    let a reply reference a message from another contact's thread. The quoted
    message must belong to the same contact.
    """
    if reply_doc.reference_doctype != "Contact" or reply_doc.reference_name != contact:
        frappe.throw(
            _("Cannot reply to a message from another conversation."),
            frappe.ValidationError,
        )


def _enrich_templates(messages: list[dict]) -> None:
    for message in messages:
        if message["message_type"] != "Template":
            continue
        if not frappe.db.exists("WhatsApp Templates", message["template"]):
            continue
        template = frappe.get_doc("WhatsApp Templates", message["template"])
        message["template_name"] = template.template_name
        template.template = _substitute_template_parameters(
            template.template, _parse_stored_params(message["template_parameters"])
        )
        message["template"] = template.template
        template.header = _substitute_template_parameters(
            template.header, _parse_stored_params(message["template_header_parameters"])
        )
        message["header"] = template.header
        message["footer"] = template.footer


def _attach_reactions(messages: list[dict]) -> None:
    """Fold each reaction onto the message it targets; the newest one wins.

    Messages arrive creation-ascending, so iterating in order lets the latest
    reaction overwrite earlier ones — matching WhatsApp, where a new reaction
    replaces the previous and an empty body clears it. Messages without a
    message_id are never indexed, so a reaction whose reply_to_message_id is
    empty can't false-match one.
    """
    by_id = _index_by_message_id(messages)
    for reaction in messages:
        if reaction["content_type"] != "reaction":
            continue
        target = by_id.get(reaction["reply_to_message_id"])
        if target:
            target["reaction"] = reaction["message"]


def _set_from_names(contact: str, messages: list[dict]) -> None:
    from_name = frappe.db.get_value("Contact", contact, "full_name") or contact
    for message in messages:
        message["from_name"] = from_name if message["from"] else _("You")


def _resolve_replies(messages: list[dict]) -> None:
    by_id = _index_by_message_id(messages)
    for reply in messages:
        if not reply.get("is_reply") or not reply.get("reply_to_message_id"):
            continue
        replied = by_id.get(reply["reply_to_message_id"])
        if not replied:
            continue
        body = replied["message"]
        if replied["message_type"] == "Template":
            body = replied["template"]
        reply["reply_message"] = body
        reply["header"] = replied.get("header") or ""
        reply["footer"] = replied.get("footer") or ""
        reply["reply_to"] = replied["name"]
        reply["reply_to_type"] = replied["type"]
        reply["reply_to_from"] = replied["from_name"]


def _index_by_message_id(messages: list[dict]) -> dict:
    """Map ``message_id`` → message, skipping messages without one so an empty
    id never becomes a lookup key."""
    return {m["message_id"]: m for m in messages if m.get("message_id")}


def _substitute_template_parameters(text: str | None, parameters: list) -> str | None:
    """Replace ``{{1}}``, ``{{2}}`` … placeholders with ``parameters`` in order.

    A template's header is optional, so ``text`` can be ``None`` while stored
    parameters survive from when the header still existed (Meta-side drift).
    There is nothing to substitute into, so return it unchanged rather than
    crashing the whole thread on ``None.replace`` — the same reason the body
    path is guarded here in one place instead of at each call site.
    """
    if not text:
        return text
    for index, parameter in enumerate(parameters, start=1):
        text = text.replace("{{" + str(index) + "}}", str(parameter))
    return text


def _parse_stored_params(value: str | None) -> list:
    """Parse stored template parameters, tolerating empty or malformed JSON.

    The parameters are written by the transport app; one bad value must not take
    down the whole thread, so a parse failure degrades to no substitution.
    """
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except (ValueError, TypeError):
        return []
    return parsed if isinstance(parsed, list) else []
