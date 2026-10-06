"""Mirror existing ticket email attachments onto their tickets.

See helpdesk.extends.file: customers read a file through its ticket row.
Oldest first, so a file sent in several emails keeps the timestamps of the
first one, like the live hook does.
"""

import frappe

from helpdesk.extends.file import mirror_to_ticket

BATCH_SIZE = 1000


def execute():
    File = frappe.qb.DocType("File")
    Communication = frappe.qb.DocType("Communication")
    query = (
        frappe.qb.from_(File)
        .join(Communication)
        .on(Communication.name == File.attached_to_name)
        .select(
            File.name,
            File.file_name,
            File.file_url,
            File.file_size,
            File.file_type,
            File.content_hash,
            File.is_private,
            File.folder,
            File.creation,
            File.modified,
            File.owner,
            File.modified_by,
            Communication.reference_name.as_("ticket"),
        )
        .where(File.attached_to_doctype == "Communication")
        .where(Communication.reference_doctype == "HD Ticket")
        .where(Communication.communication_type == "Communication")
        .orderby(File.creation)
        .orderby(File.name)
        .limit(BATCH_SIZE)
    )
    batch = query.run(as_dict=True)
    while batch:
        for row in batch:
            mirror_to_ticket(row, row.ticket)
        last = batch[-1]
        batch = query.where(
            (File.creation > last.creation)
            | ((File.creation == last.creation) & (File.name > last.name))
        ).run(as_dict=True)
