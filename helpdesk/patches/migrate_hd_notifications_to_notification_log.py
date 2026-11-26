"""HD Notification → core Notification Log, names preserved.

All rows migrate: nothing reaps Notification Log by default, so there is no
retention boundary that would make old rows pointless. Every row references
its ticket; mentions and reactions additionally carry their Comment as the
source (valid because the comments patch runs first), so a reader lands on
the exact comment. "Ticket Reopened" fixes the historical mislabel of reopen
notifications as "Reaction".
"""

import frappe
from frappe.query_builder.functions import Coalesce, Concat
from pypika import Case
from pypika.terms import ExistsCriterion, ValueWrapper

from helpdesk.patches.utils import iter_name_chunks

NOTIFICATION_COLUMNS = [
    "name",
    "creation",
    "modified",
    "modified_by",
    "owner",
    "docstatus",
    "type",
    "document_type",
    "document_name",
    "source_doctype",
    "source_name",
    "for_user",
    "from_user",
    "read",
    "subject",
    "title",
    "app",
]


def execute():
    for lower, upper in iter_name_chunks("HD Notification"):
        copy_chunk(lower, upper)
        frappe.db.commit()  # nosemgrep: sanctioned patch idiom, resumable chunks
    resolve_name_collisions()
    frappe.clear_cache()


def copy_chunk(lower: str, upper: str) -> None:
    HDNotification = frappe.qb.DocType("HD Notification")  # source
    NotificationLog = frappe.qb.DocType("Notification Log")  # target
    User = frappe.qb.DocType("User")  # full_name lookup
    existing = (
        frappe.qb.from_(NotificationLog)
        .select(NotificationLog.name)
        .where(NotificationLog.name == HDNotification.name)
    )
    from_name = Coalesce(User.full_name, HDNotification.user_from)
    (
        frappe.qb.into(NotificationLog)
        .columns(*NOTIFICATION_COLUMNS)
        .from_(HDNotification)
        .left_join(User)
        .on(User.name == HDNotification.user_from)
        .select(
            HDNotification.name,
            HDNotification.creation,
            HDNotification.modified,
            HDNotification.modified_by,
            HDNotification.owner,
            ValueWrapper(0),
            get_notification_log_type_case(HDNotification),
            ValueWrapper("HD Ticket"),
            HDNotification.reference_ticket,
            get_source_doctype_case(HDNotification),
            HDNotification.reference_comment,
            HDNotification.user_to,
            HDNotification.user_from,
            HDNotification.read,
            get_subject_case(HDNotification, from_name),
            get_subject_case(HDNotification, from_name),
            ValueWrapper("helpdesk"),
        )
        .where(HDNotification.name > lower)
        .where(HDNotification.name <= upper)
        .where(
            ExistsCriterion(existing).negate()
        )  # for each notification, only insert if it doesn't already exist in Notification Log, might have been migrated in a previous chunk or migrated in a previous run of the patch, and the patch failed for some reason, so we can resume the patch without duplicating notifications.
        .run()
    )


def get_notification_log_type_case(HDNotification) -> Case:
    return (
        Case()
        .when(HDNotification.notification_type == "Mention", "Mention")
        .when(HDNotification.notification_type == "Assignment", "Assignment")
        .when(
            (HDNotification.notification_type == "Reaction")
            & HDNotification.reference_comment.isnotnull(),
            "Reaction",
        )
        .else_("Ticket Reopened")
    )


def get_source_doctype_case(HDNotification) -> Case:
    return (
        Case().when(HDNotification.reference_comment.isnotnull(), "Comment").else_(None)
    )


def get_subject_case(HDNotification, from_name) -> Case:
    def about_ticket(verb: str):
        return Concat(
            from_name, ValueWrapper(verb + " ticket #"), HDNotification.reference_ticket
        )

    return (
        Case()
        .when(
            HDNotification.notification_type == "Mention",
            about_ticket(" mentioned you in"),
        )
        .when(
            HDNotification.notification_type == "Assignment",
            about_ticket(" assigned you"),
        )
        .when(
            (HDNotification.notification_type == "Reaction")
            & HDNotification.reference_comment.isnotnull(),
            Coalesce(HDNotification.message, ValueWrapper("reacted to your comment")),
        )
        .else_(about_ticket(" reopened"))
    )


def resolve_name_collisions() -> None:
    """Same twin check as the comments patch, on immutable creation. Nothing
    links notification names, so a fresh name is the whole fix."""
    HDNotification = frappe.qb.DocType("HD Notification")  # source
    NotificationLog = frappe.qb.DocType("Notification Log")  # target
    Twin = frappe.qb.DocType("Notification Log").as_("twin")  # migrated copy
    already_migrated = (
        frappe.qb.from_(Twin)
        .select(Twin.name)
        .where(Twin.creation == HDNotification.creation)
        .where(Twin.for_user == HDNotification.user_to)
        .where(Twin.app == "helpdesk")
    )
    # Notification not migrated yet, but its name is already taken by a migrated notification with a different creation timestamp. Reinsert the old notification under a fresh name.
    collisions = (
        frappe.qb.from_(HDNotification)
        .join(NotificationLog)
        .on(NotificationLog.name == HDNotification.name)
        .select(HDNotification.name)
        .where(NotificationLog.creation != HDNotification.creation)
        .where(
            ExistsCriterion(already_migrated).negate()
        )  # filter out already migrated notifications
        .run(pluck=True)
    )
    for old_name in collisions:
        reinsert_with_fresh_name(old_name)


def reinsert_with_fresh_name(old_name: str) -> None:
    row = frappe.db.get_value(
        "HD Notification",
        old_name,
        [
            "creation",
            "modified",
            "modified_by",
            "owner",
            "notification_type",
            "reference_ticket",
            "reference_comment",
            "user_from",
            "user_to",
            "read",
            "message",
        ],
        as_dict=True,
    )
    is_reaction = row.notification_type == "Reaction" and row.reference_comment
    if row.notification_type in ("Mention", "Assignment"):
        notification_type = row.notification_type
    elif is_reaction:
        notification_type = "Reaction"
    else:
        notification_type = "Ticket Reopened"
    from_name = frappe.utils.get_fullname(row.user_from)
    subjects = {
        "Mention": f"{from_name} mentioned you in ticket #{row.reference_ticket}",
        "Assignment": f"{from_name} assigned you ticket #{row.reference_ticket}",
        "Reaction": row.message or "reacted to your comment",
        "Ticket Reopened": f"{from_name} reopened ticket #{row.reference_ticket}",
    }
    subject = subjects[notification_type]
    NotificationLog = frappe.qb.DocType("Notification Log")  # target
    (
        frappe.qb.into(NotificationLog)
        .columns(*NOTIFICATION_COLUMNS)
        .insert(
            frappe.generate_hash(length=10),
            row.creation,
            row.modified,
            row.modified_by,
            row.owner,
            0,
            notification_type,
            "HD Ticket",
            row.reference_ticket,
            "Comment" if row.reference_comment else None,
            row.reference_comment,
            row.user_to,
            row.user_from,
            row.read,
            subject,
            subject,
            "helpdesk",
        )
        .run()
    )
