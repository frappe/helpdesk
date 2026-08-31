"""Helpdesk's funnel into core Notification Log.

Every notification helpdesk produces itself goes through here. All of them
reference the ticket; the ones about a comment additionally carry it as the
source, so a reader lands on the exact comment. Core owns the rest: per-user
enabled gate, self-notify suppression, dedupe, realtime, and the per-type
email allow-list (Reaction and Ticket Reopened are in
``notification_skip_email_types``, in-app only, as HD Notification was).

Two types are core's, not ours: mentions come from ``Comment.after_insert``
and assignments from ``assign_to``. Both reference the ticket and derive
``app="helpdesk"`` from it, so they land in the panel without our help.
"""

import frappe
from frappe import _
from frappe.desk.doctype.notification_log.notification_log import (
    enqueue_create_notification,
    set_notifications_as_unseen,
)
from frappe.utils import get_fullname

HELPDESK_APP = "helpdesk"


def notify_reaction(comment, reacting_user: str) -> None:
    """Roll reactions up into one notification for the comment author.

    "N people reacted" updates in place and re-marks unread instead of piling
    up rows, which is more than ``dedupe_on`` covers, so the existing-row
    branch is hand-rolled here.
    """
    author = comment.comment_email or comment.owner
    if author == reacting_user:
        return
    reacting_users = {r.user for r in comment.reactions if r.user != author}
    if not reacting_users:
        return
    count = len(reacting_users)
    if count == 1:
        message = _("1 person reacted to your comment")
    else:
        message = _("{0} people reacted to your comment").format(count)

    existing = frappe.db.get_value(
        "Notification Log",
        {
            "type": "Reaction",
            "source_doctype": "Comment",
            "source_name": comment.name,
            "for_user": author,
        },
        "name",
    )
    if existing:
        frappe.db.set_value(
            "Notification Log",
            existing,
            {
                "subject": message,
                "title": message,
                "from_user": reacting_user,
                "read": 0,
            },
            update_modified=False,
        )
        frappe.publish_realtime("notification", after_commit=True, user=author)
        set_notifications_as_unseen(author)
        return
    enqueue_create_notification(
        [author],
        {
            "type": "Reaction",
            "document_type": "HD Ticket",
            "document_name": comment.reference_name,
            "source_doctype": "Comment",
            "source_name": comment.name,
            "subject": message,
            "from_user": reacting_user,
            "app": HELPDESK_APP,
        },
    )


@frappe.whitelist()
def clear(ticket: str | None = None, comment: str | None = None) -> None:
    """Mark the session user's helpdesk notifications as read.

    Every helpdesk notification references the ticket, so clearing one covers
    its comment notifications too.
    """
    filters = {"for_user": frappe.session.user, "read": 0, "app": HELPDESK_APP}
    if comment:
        mark_read({**filters, "source_doctype": "Comment", "source_name": comment})
        return
    if ticket:
        mark_read({**filters, "document_type": "HD Ticket", "document_name": ticket})
        return
    mark_read(filters)


def mark_read(filters: dict) -> None:
    frappe.db.set_value("Notification Log", filters, "read", 1, update_modified=False)


def notify_ticket_reopened(ticket: str, agents: list[str]) -> None:
    """Notify assigned agents that a resolved ticket went back to Open."""
    if not agents:
        return
    enqueue_create_notification(
        agents,
        {
            "type": "Ticket Reopened",
            "document_type": "HD Ticket",
            "document_name": ticket,
            "subject": _("{0} reopened ticket #{1}").format(
                get_fullname(frappe.session.user), ticket
            ),
            "from_user": frappe.session.user,
            "app": HELPDESK_APP,
        },
    )
