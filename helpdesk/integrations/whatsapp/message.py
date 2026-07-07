"""``WhatsApp Message`` document events.

Wired from ``hooks.py`` (``doc_events``), these run only when the frappe_whatsapp
transport app is installed. They anchor every message on a ``Contact`` and
surface it to agents in real time.
"""

import frappe
from frappe.desk.form.assign_to import get as get_assignees

from helpdesk.integrations.whatsapp.utils import (
    counterparty_number,
    get_open_tickets_for_contact,
    resolve_or_create_contact,
)
from helpdesk.utils import get_doc_room, publish_event

NEW_MESSAGE_EVENT = "helpdesk:new-whatsapp-message"

# The out-of-band re-anchor is itself the safety net for an unlinked inbound
# message, so it must not die silently and orphan the message: it reschedules on
# failure up to this many attempts, then gives up visibly (Error Log).
MAX_ANCHOR_ATTEMPTS = 5


def validate(doc, method=None):
    """Anchor the message on a Contact (omnichannel) and on its open ticket.

    A message already anchored by the sending API is left untouched. Anchoring
    runs inside the transport's webhook, which inserts inbound messages in a
    loop with no per-message guard — and an unhandled exception in a Frappe
    request rolls back the *entire* batch. So a failure here must not raise: the
    message is inserted unlinked and :func:`after_insert` schedules a retry, so
    it is never lost and no sibling message is dropped.
    """
    if doc.reference_doctype and doc.reference_name:
        return

    number = counterparty_number(doc)
    if not number:
        return

    try:
        _anchor_on_contact(doc, number)
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Helpdesk WhatsApp: failed to anchor message on contact",
        )


def after_insert(doc, method=None):
    """Surface an anchored message, or schedule a retry for an unlinked one.

    Side effects are best-effort and never propagate, for the same batch-safety
    reason as :func:`validate`.
    """
    if doc.reference_doctype == "Contact" and doc.reference_name:
        _run_side_effects(doc)
        return

    # Unlinked inbound message: anchoring failed in validate. Retry out of band
    # so it is never lost, without aborting the webhook batch.
    if doc.type == "Incoming" and counterparty_number(doc):
        _schedule_reanchor(doc.name, attempt=1)


def reanchor_message(message_name: str, attempt: int = 1):
    """Background retry of anchoring for a message the webhook left unlinked.

    Enqueued by :func:`after_insert`. Persists the anchor with ``db_set`` (the
    document is already inserted) and then runs the surfacing side effects.

    This job is the safety net for an unlinked message, so it must not orphan it
    by dying: if resolving the contact raises again (a transient DB error, a
    lock during a concurrent create), it is caught and the job reschedules,
    bounded by :data:`MAX_ANCHOR_ATTEMPTS`. On exhaustion it logs and stops
    rather than looping — the message stays queryable in the Error Log for
    manual recovery instead of failing invisibly.
    """
    doc = frappe.get_doc("WhatsApp Message", message_name)
    if doc.reference_doctype and doc.reference_name:
        return

    number = counterparty_number(doc)
    if not number:
        return  # no number to anchor on; no retry can invent one

    try:
        anchored = _anchor_on_contact(doc, number)
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Helpdesk WhatsApp: re-anchor attempt failed",
        )
        anchored = False

    if not anchored:
        _retry_or_give_up(message_name, attempt)
        return

    updates = {
        "reference_doctype": doc.reference_doctype,
        "reference_name": doc.reference_name,
    }
    if _has_ticket_link():
        updates["hd_ticket"] = doc.get("hd_ticket")
    doc.db_set(updates, update_modified=False)

    _run_side_effects(doc)


def _schedule_reanchor(message_name: str, attempt: int):
    """Enqueue the out-of-band anchoring retry for an unlinked message."""
    frappe.enqueue(
        "helpdesk.integrations.whatsapp.message.reanchor_message",
        enqueue_after_commit=True,
        queue="short",
        message_name=message_name,
        attempt=attempt,
    )


def _retry_or_give_up(message_name: str, attempt: int):
    """Reschedule the anchoring retry, or log and stop once the cap is hit."""
    if attempt >= MAX_ANCHOR_ATTEMPTS:
        frappe.log_error(
            f"WhatsApp Message {message_name} could not be anchored on a "
            f"contact after {attempt} attempts; it stays out of every thread "
            f"until its number resolves. Re-run reanchor_message to recover.",
            "Helpdesk WhatsApp: gave up anchoring message",
        )
        return
    _schedule_reanchor(message_name, attempt + 1)


def _anchor_on_contact(doc, number: str) -> bool:
    """Resolve ``number`` to a Contact and anchor ``doc`` on it in memory.

    Also attributes an inbound message to the contact's most recent open ticket.
    Returns ``True`` when a contact was resolved and set.
    """
    contact = resolve_or_create_contact(number)
    if not contact:
        return False

    doc.reference_doctype = "Contact"
    doc.reference_name = contact

    if doc.type == "Incoming" and not doc.get("hd_ticket") and _has_ticket_link():
        open_tickets = get_open_tickets_for_contact(contact)
        if open_tickets:
            doc.hd_ticket = open_tickets[0]
    return True


def _has_ticket_link() -> bool:
    """Whether the ``hd_ticket`` Custom Field has been migrated in yet."""
    return frappe.db.has_column("WhatsApp Message", "hd_ticket")


def _run_side_effects(doc):
    """Broadcast the message and notify agents — best-effort, never propagates."""
    try:
        _broadcast(doc)
        if doc.type == "Incoming":
            _notify_agents(doc)
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Helpdesk WhatsApp: post-insert side effects failed",
        )


def _broadcast(doc):
    """Realtime nudge so the Contact thread and any open ticket refetch."""
    contact = doc.reference_name
    payload = {"contact": contact, "whatsapp_message": doc.name}

    publish_event(
        NEW_MESSAGE_EVENT, room=get_doc_room("Contact", contact), data=payload
    )
    for ticket in get_open_tickets_for_contact(contact):
        publish_event(
            NEW_MESSAGE_EVENT,
            room=get_doc_room("HD Ticket", ticket),
            data={**payload, "ticket_id": ticket},
        )


def _notify_agents(doc):
    """One HD Notification per agent assigned to an open ticket of the contact.

    A message with no open ticket is pure conversation — it still lands on the
    Contact thread, but raises no ticket notification.
    """
    notified: set[str] = set()
    for ticket in get_open_tickets_for_contact(doc.reference_name):
        for assignee in get_assignees({"doctype": "HD Ticket", "name": ticket}):
            user = assignee.owner
            if user == doc.owner or user in notified:
                continue
            notified.add(user)
            frappe.get_doc(
                {
                    "doctype": "HD Notification",
                    "user_from": doc.owner,
                    "user_to": user,
                    "notification_type": "WhatsApp",
                    "reference_ticket": ticket,
                    "message": doc.message,
                }
            ).insert(ignore_permissions=True)
