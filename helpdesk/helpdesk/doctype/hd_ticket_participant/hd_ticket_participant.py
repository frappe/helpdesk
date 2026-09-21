# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

import hashlib

import frappe
from frappe.model.document import Document


def participant_name(ticket: str, email: str, role: str) -> str:
    """Name a participant row from its own contents.

    Both writers insert blindly: a repeat resolves to the same name and is
    ignored rather than duplicating, so neither the inbound-email hook nor
    the backfill needs an exists() round trip or a composite unique index.
    The backfill writes through bulk_insert and so never runs autoname(),
    which is why this lives at module level instead of on the class.
    """
    return hashlib.sha256(
        f"{ticket}:{normalize_email(email)}:{role}".encode()
    ).hexdigest()[:20]


def normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def on_ticket_trash(doc, method: str | None = None) -> None:
    """Clear a ticket's participants as it is deleted.

    These rows hold a Link to HD Ticket, so without this core refuses the
    delete as still linked. on_trash runs ahead of check_if_doc_is_linked
    (see frappe/model/delete_doc.py), so clearing them here is enough.
    """
    frappe.db.delete("HD Ticket Participant", {"ticket": doc.name})


class HDTicketParticipant(Document):
    def autoname(self):
        # Normalised here rather than in validate(): autoname runs first, and
        # the name has to be derived from the same value that gets stored.
        self.email = normalize_email(self.email)
        self.name = participant_name(self.ticket, self.email, self.role)
