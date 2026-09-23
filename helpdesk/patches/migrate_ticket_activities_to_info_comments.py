"""Migrate to Info comments the HD Ticket Activity rows whose only copy is that table.

Tag changes, auto-close reasons, and split markers never saved the ticket, so
no Version row exists; they become backdated Info comments. Field-change rows
stay behind by design: Version rows (track_changes since 2019) already cover
them, and migrating both would double every status change in the feed.
"""

import frappe
from pypika import Criterion
from pypika.terms import ExistsCriterion, ValueWrapper

from helpdesk.patches.utils import iter_name_chunks

MIGRATED_ACTION_PREFIXES = [
    "added tag%",
    "removed tag%",
    "automatically closed%",
    "split the ticket%",
]


def execute():
    # chunk over the whole table; the prefix filter lives in the insert-select
    for lower, upper in iter_name_chunks("HD Ticket Activity"):
        copy_chunk(lower, upper)
        frappe.db.commit()  # nosemgrep: sanctioned patch idiom, resumable chunks
    resolve_name_collisions()


def copy_chunk(lower: str, upper: str) -> None:
    HDTicketActivity = frappe.qb.DocType("HD Ticket Activity")  # source
    Comment = frappe.qb.DocType("Comment")  # target
    existing = (
        frappe.qb.from_(Comment)
        .select(Comment.name)
        .where(Comment.name == HDTicketActivity.name)
    )
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
        )
        .from_(HDTicketActivity)
        .select(
            HDTicketActivity.name,
            HDTicketActivity.creation,
            HDTicketActivity.modified,
            HDTicketActivity.modified_by,
            HDTicketActivity.owner,
            ValueWrapper(0),
            ValueWrapper("Info"),
            HDTicketActivity.owner,
            HDTicketActivity.action,
            ValueWrapper("HD Ticket"),
            HDTicketActivity.ticket,
        )
        .where(HDTicketActivity.name > lower)
        .where(HDTicketActivity.name <= upper)
        .where(migrated_actions_criterion(HDTicketActivity))
        .where(ExistsCriterion(existing).negate())
        .run()
    )


def migrated_actions_criterion(HDTicketActivity) -> Criterion:
    return Criterion.any(
        HDTicketActivity.action.like(prefix) for prefix in MIGRATED_ACTION_PREFIXES
    )


def resolve_name_collisions() -> None:
    """Activity and comment names come from the same hash space, so a migrated
    row's name may already belong to a migrated comment. Same twin check as
    the comments patch; nothing external links activity names, so a fresh
    name is enough."""
    HDTicketActivity = frappe.qb.DocType("HD Ticket Activity")  # source
    Comment = frappe.qb.DocType("Comment")  # target
    Twin = frappe.qb.DocType("Comment").as_("twin")  # migrated copy
    already_migrated = (
        frappe.qb.from_(Twin)
        .select(Twin.name)
        .where(Twin.creation == HDTicketActivity.creation)
        .where(Twin.reference_doctype == "HD Ticket")
        .where(Twin.comment_type == "Info")
        .where(Twin.owner == HDTicketActivity.owner)
    )
    collisions = (
        frappe.qb.from_(HDTicketActivity)
        .join(Comment)
        .on(Comment.name == HDTicketActivity.name)
        .select(HDTicketActivity.name)
        .where(migrated_actions_criterion(HDTicketActivity))
        .where(
            (Comment.creation != HDTicketActivity.creation)
            | (Comment.comment_type != "Info")
        )
        .where(ExistsCriterion(already_migrated).negate())
        .run(pluck=True)
    )
    for old_name in collisions:
        reinsert_with_fresh_name(old_name)


def reinsert_with_fresh_name(old_name: str) -> None:
    row = frappe.db.get_value(
        "HD Ticket Activity",
        old_name,
        ["creation", "modified", "modified_by", "owner", "action", "ticket"],
        as_dict=True,
    )
    Comment = frappe.qb.DocType("Comment")  # target
    new_name = frappe.generate_hash(length=10)
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
        )
        .insert(
            new_name,
            row.creation,
            row.modified,
            row.modified_by,
            row.owner,
            0,
            "Info",
            row.owner,
            row.action,
            "HD Ticket",
            row.ticket,
        )
        .run()
    )
    frappe.log_error(
        title="Activity migration rename",
        message=f"HD Ticket Activity {old_name} collided with an existing Comment; migrated as {new_name}",
    )
