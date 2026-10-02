"""File rules for HD Ticket emails.

Email attachments hang off the Communication, which customers cannot read.
Customers can read their ticket, so a second row on the ticket makes the same
url servable to them (see frappe's `find_file_by_url`). Comments stay agent-only:
only files of customer-visible emails are mirrored.
"""

import re

import frappe

FID_PATTERN = re.compile(r"(/private/files/[^\"'?#\s]+)\?fid=([A-Za-z0-9]+)")


def after_insert(doc, method: str | None = None):
    if ticket := email_ticket(doc.attached_to_doctype, doc.attached_to_name):
        mirror_to_ticket(doc, ticket)


def email_ticket(doctype: str | None, name: str | None) -> str | None:
    """The ticket an email belongs to, if the file hangs off a ticket email."""
    if doctype != "Communication" or not name:
        return None
    email = frappe.db.get_value(
        "Communication",
        name,
        ["reference_doctype", "reference_name", "communication_type"],
        as_dict=True,
    )
    if not email or email.reference_doctype != "HD Ticket":
        return None
    if email.communication_type != "Communication":
        return None
    return email.reference_name


def mirror_to_ticket(file, ticket: str):
    """Insert the row directly: saving a File with a url can copy the content
    to a new url, and would stamp a second Attachment comment on the ticket.
    The mirror keeps the file's timestamps, since split_ticket moves ticket
    files by creation together with the emails they belong to."""
    if frappe.db.exists(
        "File",
        {
            "file_url": file.file_url,
            "attached_to_doctype": "HD Ticket",
            "attached_to_name": ticket,
        },
    ):
        return
    mirror = frappe.new_doc("File")
    mirror.update(
        {
            "file_name": file.file_name,
            "file_url": file.file_url,
            "file_size": file.file_size,
            "file_type": file.file_type,
            "content_hash": file.content_hash,
            "is_private": file.is_private,
            "folder": file.folder,
            "attached_to_doctype": "HD Ticket",
            "attached_to_name": ticket,
            "creation": file.creation,
            "modified": file.modified,
            "owner": file.owner,
            "modified_by": file.modified_by,
        }
    )
    mirror.set_new_name()
    mirror.db_insert()


def strip_email_file_ids(emails: list[dict]) -> None:
    """Inline images pin the Communication's row via `fid`, which customers
    cannot read; without it the ticket's mirror row serves the url.

    `emails` are the Communications of a ticket the caller may read, with name
    and content; their content is changed in place. One File query covers all
    of them and stays within that ticket."""
    fids = {
        m.group(2)
        for email in emails
        for m in FID_PATTERN.finditer(email.get("content") or "")
    }
    if not fids:
        return
    on_emails = set(
        frappe.get_all(
            "File",
            filters={
                "name": ["in", list(fids)],
                "attached_to_doctype": "Communication",
                "attached_to_name": ["in", [email["name"] for email in emails]],
            },
            pluck="name",
        )
    )
    for email in emails:
        if email.get("content"):
            email["content"] = FID_PATTERN.sub(
                lambda m: m.group(1) if m.group(2) in on_emails else m.group(0),
                email["content"],
            )
