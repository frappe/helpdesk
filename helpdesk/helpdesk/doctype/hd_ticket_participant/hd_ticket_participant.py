# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

import hashlib

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


class HDTicketParticipant(Document):
    def autoname(self):
        # Normalised here rather than in validate(): autoname runs first, and
        # the name has to be derived from the same value that gets stored.
        self.email = normalize_email(self.email)
        self.name = participant_name(self.ticket, self.email, self.role)
