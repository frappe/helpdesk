"""Record who was on a ticket's email thread.

The To/Cc/From lines live on Communication as raw comma-joined header
strings, which can only be searched by substring. Projecting them into
HD Ticket Participant rows turns "which tickets is this person involved
in" into an indexed equality lookup.

Communication stays the source of truth; these rows are a derived index
and can be rebuilt from it at any time.
"""

from email.utils import getaddresses

import frappe

from helpdesk.helpdesk.doctype.hd_ticket_participant.hd_ticket_participant import (
    normalize_email,
)

ROLES_BY_FIELD = {"recipients": "To", "cc": "Cc", "sender": "From"}


def after_insert(doc, method: str | None = None):
    """Deliberately swallows its own failures.

    This runs while an inbound email is being attached to a ticket. Mail
    from the wild carries malformed headers, and raising here would stop
    that email reaching the ticket at all. A missing participant row costs
    a row in the Related Tickets tab and is repaired by re-running the
    backfill; a rejected email loses a customer's message.
    """
    if doc.reference_doctype != "HD Ticket" or not doc.reference_name:
        return
    try:
        record_participants(doc)
    except Exception:
        frappe.log_error(
            title="Ticket participant capture failed",
            message=f"Communication {doc.name} on {doc.reference_name}",
        )


def record_participants(doc) -> None:
    for email, role in participants_of(doc):
        frappe.get_doc(
            {
                "doctype": "HD Ticket Participant",
                "ticket": doc.reference_name,
                "email": email,
                "role": role,
            }
        ).insert(ignore_permissions=True, ignore_if_duplicate=True)


def participants_of(doc) -> set[tuple[str, str]]:
    """The (address, role) pairs named on a communication's headers."""
    found = set()
    for field, role in ROLES_BY_FIELD.items():
        header = doc.get(field)
        if not header:
            continue
        # getaddresses over a naive split(','): display names are allowed to
        # contain commas when quoted, as in '"Doe, Kelly" <kelly@work.com>'.
        for _display_name, address in getaddresses([header]):
            address = normalize_email(address)
            # Headers carry group syntax and bare labels too
            # ('undisclosed-recipients:;'), which parse to non-addresses.
            if "@" in address:
                found.add((address, role))
    return found
