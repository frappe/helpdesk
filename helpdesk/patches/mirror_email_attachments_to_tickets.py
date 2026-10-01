"""Mirror existing ticket email attachments onto their tickets.

See helpdesk.extends.file: customers read a file through its ticket row.
"""

import frappe

from helpdesk.extends.file import mirror_to_ticket


def execute():
    File = frappe.qb.DocType("File")
    Communication = frappe.qb.DocType("Communication")
    rows = (
        frappe.qb.from_(File)
        .join(Communication)
        .on(Communication.name == File.attached_to_name)
        .select(
            File.file_name,
            File.file_url,
            File.file_size,
            File.file_type,
            File.content_hash,
            File.is_private,
            File.folder,
            Communication.reference_name.as_("ticket"),
        )
        .where(File.attached_to_doctype == "Communication")
        .where(Communication.reference_doctype == "HD Ticket")
        .where(Communication.communication_type == "Communication")
        .run(as_dict=True)
    )
    for row in rows:
        mirror_to_ticket(row, row.ticket)
