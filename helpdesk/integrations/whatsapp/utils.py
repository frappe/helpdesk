"""Shared helpers for the WhatsApp integration.

The integration is *omnichannel*: a conversation is anchored on the core
``Contact`` (shared with ERPNext/CRM on the same site), not on a ticket. A
ticket is the unit of work that grows out of a conversation when there is
support to do; the thread itself belongs to the person. Every helper here is
inert when ``frappe_whatsapp`` is not installed, so Helpdesk keeps working
without the transport app.
"""

import frappe
from frappe import _
from frappe.query_builder import Order
from pypika.functions import Replace

from helpdesk.utils import is_agent, parse_phone_number

# The WhatsApp DocTypes provided by the frappe_whatsapp transport app.
WHATSAPP_MESSAGE = "WhatsApp Message"
WHATSAPP_SETTINGS = "WhatsApp Settings"

# Formatting characters stripped from a phone number before comparison. The
# same set is applied to the inbound number and (in SQL) to the stored number,
# so both sides normalize identically.
_PHONE_NOISE = (" ", "-", "(", ")", "+")


def counterparty_number(doc) -> str | None:
    """The other party's number on a message: ``from`` inbound, ``to`` outbound."""
    return doc.get("from") if doc.type == "Incoming" else doc.get("to")


def _strip_phone_formatting(number: str) -> str:
    for char in _PHONE_NOISE:
        number = number.replace(char, "")
    return number


def is_whatsapp_installed() -> bool:
    """Whether the frappe_whatsapp transport app is installed on the site."""
    return bool(frappe.db.exists("DocType", WHATSAPP_MESSAGE))


def is_whatsapp_enabled() -> bool:
    """Whether an active outgoing WhatsApp account is configured."""
    if not frappe.db.exists("DocType", WHATSAPP_SETTINGS):
        return False
    default_outgoing = frappe.get_cached_value(
        WHATSAPP_SETTINGS, WHATSAPP_SETTINGS, "default_outgoing_account"
    )
    if not default_outgoing:
        return False
    status = frappe.get_cached_value("WhatsApp Account", default_outgoing, "status")
    return status == "Active"


def resolve_or_create_contact(number: str) -> str | None:
    """Resolve a phone number to a ``Contact``, creating one when unknown.

    This is the heart of the omnichannel model: every WhatsApp message binds to
    a Contact from message #1, so a conversation always has an identity even
    before any ticket exists. A number that matches no existing Contact yields a
    minimal "unknown" Contact carrying just the number, enrichable later.

    :param number: The counterparty's phone number (E.164 or local).
    :return: The Contact ``name``, or ``None`` when the number is blank.
    """
    if not number or not number.strip():
        return None

    contact = _find_contact_by_number(number)
    if contact:
        return contact

    return _create_unknown_contact(number)


def _find_contact_by_number(number: str) -> str | None:
    """Exact-match ``number`` to a Contact through its phone rows.

    Deliberately NOT the substring ``LIKE`` used for call-log display
    (:func:`helpdesk.utils.get_contact_by_phone_number`): here the match drives
    silent auto-anchoring and ticket attribution, so a contact whose number
    merely *contains* these digits would misroute the whole conversation and let
    an agent reply to the wrong customer. We require normalized (digits-only)
    equality against ``Contact Phone.phone``.
    """
    cleaned = _strip_phone_formatting(number)
    if not cleaned:
        return None

    contact_phone = frappe.qb.DocType("Contact Phone")
    normalized = contact_phone.phone
    for char in _PHONE_NOISE:
        normalized = Replace(normalized, char, "")

    rows = (
        frappe.qb.from_(contact_phone)
        .select(contact_phone.parent)
        .where(normalized == cleaned)
        .orderby(contact_phone.modified, order=Order.desc)
        .run(as_dict=True)
    )
    return rows[0]["parent"] if rows else None


def _create_unknown_contact(number: str) -> str:
    """Create a minimal Contact anchored on ``number``.

    The number is stored as both the primary phone and the primary mobile so
    later lookups resolve, and is used as the display name until an agent
    enriches the record.
    """
    parsed = parse_phone_number(number)
    stored_number = (
        parsed.get("formats", {}).get("E164", number)
        if parsed.get("success")
        else number
    )

    doc = frappe.new_doc("Contact")
    doc.first_name = stored_number
    doc.append(
        "phone_nos",
        {"phone": stored_number, "is_primary_phone": 1, "is_primary_mobile_no": 1},
    )
    doc.insert(ignore_permissions=True)
    return doc.name


def validate_whatsapp_access(
    reference_doctype: str | None = None,
    reference_name: str | None = None,
    permtype: str = "read",
) -> None:
    """Gate WhatsApp features to agents, and check reference-doc permission.

    :param reference_doctype: DocType of the anchored record (``Contact``).
    :param reference_name: Name of the anchored record.
    :param permtype: Permission to require on the reference document.
    """
    if not is_agent():
        frappe.throw(
            _("Only agents can access WhatsApp features."), frappe.PermissionError
        )

    if reference_doctype and reference_name:
        if not frappe.db.exists(reference_doctype, reference_name):
            frappe.throw(
                _("Reference document {0} {1} does not exist.").format(
                    reference_doctype, reference_name
                ),
                frappe.DoesNotExistError,
            )
        if not frappe.has_permission(reference_doctype, permtype, reference_name):
            frappe.throw(
                _("Not permitted to access reference document {0} {1}.").format(
                    reference_doctype, reference_name
                ),
                frappe.PermissionError,
            )


def get_open_tickets_for_contact(contact: str) -> list[str]:
    """Open HD Tickets linked to ``contact``, most recently touched first.

    The ordering matters: an inbound message with no explicit ticket is
    attributed to the contact's most recent open ticket (the first element).
    """
    if not contact:
        return []
    return frappe.get_all(
        "HD Ticket",
        filters={"contact": contact, "status": ["not in", ["Closed", "Resolved"]]},
        order_by="modified desc",
        pluck="name",
    )


def get_contact_whatsapp_number(contact: str) -> str | None:
    """The destination number for ``contact``, resolved server-side.

    The send APIs never trust a client-supplied number: an agent must not be
    able to use Helpdesk as a gateway to an arbitrary destination. The number is
    always the contact's own primary mobile (or phone).
    """
    values = frappe.db.get_value("Contact", contact, ["mobile_no", "phone"])
    if not values:
        return None
    mobile, phone = values
    return mobile or phone


def assert_ticket_belongs_to_contact(hd_ticket: str | None, contact: str) -> None:
    """Reject tagging a message onto a ticket the contact does not own.

    Without this an agent could attribute an outbound message to any ticket id,
    including tickets of other customers. An empty ``hd_ticket`` is fine.
    """
    if not hd_ticket:
        return
    ticket_contact = frappe.db.get_value("HD Ticket", hd_ticket, "contact")
    if ticket_contact != contact:
        frappe.throw(
            _("Ticket {0} does not belong to this contact.").format(hd_ticket),
            frappe.ValidationError,
        )
