"""Project the email headers already on tickets into participant rows.

Safe to re-run: rows are named from their contents, so a batch that
already landed is ignored rather than duplicated. That matters because a
site with a large Communication table may not get through this in one
migrate window.

Writes go through bulk_insert rather than the document API, which means
no link validation: a row whose ticket has since been deleted is
inserted as an orphan. That is harmless, since get_related_tickets feeds
these names into a permission-checked HD Ticket lookup that simply won't
match them.
"""

import frappe
from frappe.utils import now

from helpdesk.extends.communication import participants_of
from helpdesk.helpdesk.doctype.hd_ticket_participant.hd_ticket_participant import (
    participant_name,
)

BATCH_SIZE = 5000
FIELDS = [
    "name",
    "ticket",
    "email",
    "role",
    "creation",
    "modified",
    "owner",
    "modified_by",
]


def execute():
    timestamp = now()
    cursor = ""

    while True:
        communications = frappe.get_all(
            "Communication",
            filters={"reference_doctype": "HD Ticket", "name": [">", cursor]},
            fields=["name", "reference_name", "recipients", "cc", "sender"],
            order_by="name asc",
            limit=BATCH_SIZE,
        )
        if not communications:
            break

        rows = _rows_for(communications, timestamp)
        if rows:
            frappe.db.bulk_insert(
                "HD Ticket Participant",
                fields=FIELDS,
                values=list(rows.values()),
                ignore_duplicates=True,
            )
        # Per batch, so a run that is interrupted leaves less to redo.
        frappe.db.commit()
        cursor = communications[-1].name


def _rows_for(communications: list, timestamp: str) -> dict:
    """Keyed by participant name, so one person copied on many replies in
    the same batch collapses to a single row before it reaches the insert."""
    rows = {}
    for communication in communications:
        ticket = communication.reference_name
        if not ticket:
            continue
        for email, role in participants_of(communication):
            name = participant_name(ticket, email, role)
            rows[name] = (
                name,
                ticket,
                email,
                role,
                timestamp,
                timestamp,
                "Administrator",
                "Administrator",
            )
    return rows
