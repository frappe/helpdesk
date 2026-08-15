"""HD Ticket Comment → core Comment, names preserved.

Set-based insert-select: every foreign link (files, reactions, notifications,
``?highlight=comment-<name>`` deep links) already carries the comment's name,
so nothing is rewritten. NOT EXISTS skips migrated rows, which also makes an
interrupted migrate resume cleanly. No controller methods: they would restamp
modified, regenerate names, and refire mention notifications.
"""

import frappe
from frappe.query_builder.functions import Coalesce
from pypika.terms import ExistsCriterion, ValueWrapper

from helpdesk.patches.utils import iter_name_chunks


def execute():
    for lower, upper in iter_name_chunks("HD Ticket Comment"):  # 50_000 rows per chunk
        copy_chunk(lower, upper)  # migrate a chunk of HD Ticket Comments to Comment
        frappe.db.commit()  # nosemgrep: sanctioned patch idiom, resumable chunks
    resolve_name_collisions()  # hash collision


def copy_chunk(lower: str, upper: str) -> None:
    HDTicketComment = frappe.qb.DocType("HD Ticket Comment")  # source
    Comment = frappe.qb.DocType("Comment")  # target
    User = frappe.qb.DocType("User")  # full_name lookup, needed for comment
    existing = (
        frappe.qb.from_(Comment)
        .select(Comment.name)
        .where(Comment.name == HDTicketComment.name)
    )  # subquery for NOT EXISTS to skip already migrated rows

    (
        frappe.qb.into(Comment)
        .columns(
            "name",
            "creation",
            "modified",
            "modified_by",
            "owner",
            "docstatus",
            "comment_type",
            "comment_email",
            "comment_by",
            "content",
            "reference_doctype",
            "reference_name",
            "is_pinned",
        )
        .from_(HDTicketComment)
        .left_join(User)
        .on(User.name == HDTicketComment.commented_by)
        .select(
            HDTicketComment.name,
            HDTicketComment.creation,
            HDTicketComment.modified,
            HDTicketComment.modified_by,
            HDTicketComment.owner,
            ValueWrapper(0),
            ValueWrapper("Comment"),
            Coalesce(HDTicketComment.commented_by, HDTicketComment.owner),
            User.full_name,
            HDTicketComment.content,
            ValueWrapper("HD Ticket"),
            HDTicketComment.reference_ticket,
            HDTicketComment.is_pinned,
        )
        .where(HDTicketComment.name > lower)
        .where(HDTicketComment.name <= upper)
        .where(ExistsCriterion(existing).negate())  # skip already migrated rows
        .run()
    )


def resolve_name_collisions() -> None:
    """Re-insert rows whose name is taken by a stranger (hash collision).

    NOT EXISTS can't tell "already migrated" from "collision", so compare the
    twin on immutable fields: same name but different creation (or a non-ticket
    reference) means a foreign row owns the name. reference_name is deliberately
    not compared; split_ticket legitimately moves migrated comments to a new
    ticket. Expected result: zero rows. Stragglers get a fresh name, their
    legacy-table links are re-pointed, and the rename is logged (one dead
    highlight anchor accepted).
    """
    HDTicketComment = frappe.qb.DocType("HD Ticket Comment")  # source
    Comment = frappe.qb.DocType("Comment")  # target
    Twin = frappe.qb.DocType("Comment").as_("twin")  # migrated copy
    # a previous run may have already re-inserted this row under a fresh name;
    # its immutable creation identifies it regardless of name
    already_migrated = (
        frappe.qb.from_(Twin)
        .select(Twin.name)
        .where(Twin.creation == HDTicketComment.creation)
        .where(Twin.reference_doctype == "HD Ticket")
        .where(Twin.comment_type == "Comment")
        .where(Twin.owner == HDTicketComment.owner)
    )
    collisions = (
        frappe.qb.from_(HDTicketComment)
        .join(Comment)
        .on(Comment.name == HDTicketComment.name)
        .select(HDTicketComment.name)
        .where(
            (Comment.creation != HDTicketComment.creation)
            | (Comment.reference_doctype != "HD Ticket")
        )
        .where(ExistsCriterion(already_migrated).negate())
        .run(pluck=True)
    )
    for old_name in collisions:
        reinsert_with_fresh_name(old_name)


# take the new name and re-point the legacy table's links (reactions, files, notifications) to it
def reinsert_with_fresh_name(old_name: str) -> None:
    row = frappe.db.get_value(
        "HD Ticket Comment",
        old_name,
        [
            "name",
            "creation",
            "modified",
            "modified_by",
            "owner",
            "commented_by",
            "content",
            "reference_ticket",
            "is_pinned",
        ],
        as_dict=True,
    )
    new_name = frappe.generate_hash(length=10)
    Comment = frappe.qb.DocType("Comment")  # target
    (
        frappe.qb.into(Comment)
        .columns(
            "name",
            "creation",
            "modified",
            "modified_by",
            "owner",
            "docstatus",
            "comment_type",
            "comment_email",
            "content",
            "reference_doctype",
            "reference_name",
            "is_pinned",
        )
        .insert(
            new_name,
            row.creation,
            row.modified,
            row.modified_by,
            row.owner,
            0,
            "Comment",
            row.commented_by or row.owner,
            row.content,
            "HD Ticket",
            row.reference_ticket,
            row.is_pinned,
        )
        .run()
    )
    # if hash / name 123 (from hd_ticket_comment) is taken by a comment named 123, then migrated comment must be reinserted under a fresh name. The legacy table's links (reactions, files, notifications) still point to the old name, so they must be re-pointed to the new name.
    relink_legacy_references(old_name, new_name)
    frappe.log_error(
        title="Comment migration rename",
        message=f"HD Ticket Comment {old_name} collided with an existing Comment; migrated as {new_name}",
    )


def relink_legacy_references(old_name: str, new_name: str) -> None:
    """Later patches carry these links verbatim, so fix them pre-flight."""
    frappe.db.set_value(
        "HD Comment Reaction",
        {"parent": old_name, "parenttype": "HD Ticket Comment"},
        "parent",
        new_name,
        update_modified=False,
    )
    frappe.db.set_value(
        "File",
        {"attached_to_doctype": "HD Ticket Comment", "attached_to_name": old_name},
        "attached_to_name",
        new_name,
        update_modified=False,
    )
    frappe.db.set_value(
        "HD Notification",
        {"reference_comment": old_name},
        "reference_comment",
        new_name,
        update_modified=False,
    )
