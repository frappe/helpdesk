"""Helpdesk notifications, written to core Notification Log.

Every row references the ticket. Comment notifications also carry the comment as
source so the reader lands on it. Core handles the per-user gate, self-notify
suppression, dedupe, realtime and email. Mentions and assignments are created by
core itself.
"""

import frappe
from frappe import _
from frappe.desk.doctype.notification_log.notification_log import (
    enqueue_create_notification,
    make_notification_logs,
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
    if not reacting_users:
        if existing:
            frappe.db.delete("Notification Log", {"name": existing})
            frappe.publish_realtime("notification", after_commit=True, user=author)
        return
    count = len(reacting_users)
    if count == 1:
        message = _("1 person reacted to your comment")
    else:
        message = _("{0} people reacted to your comment").format(count)

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
    # inserted in-request, not enqueued: the existence check above must see it
    make_notification_logs(
        frappe._dict(
            type="Reaction",
            document_type="HD Ticket",
            document_name=comment.reference_name,
            source_doctype="Comment",
            source_name=comment.name,
            subject=message,
            from_user=reacting_user,
            app=HELPDESK_APP,
        ),
        [author],
    )


@frappe.whitelist()
def clear(ticket: str | None = None, comment: str | None = None) -> int:
    """Mark the session user's helpdesk notifications as read.

    Every helpdesk notification references the ticket, so clearing one covers
    its comment notifications too.
    """
    filters = {"for_user": frappe.session.user, "read": 0, "app": HELPDESK_APP}
    if comment:
        return mark_read(
            {**filters, "source_doctype": "Comment", "source_name": comment}
        )
    if ticket:
        return mark_read(
            {**filters, "document_type": "HD Ticket", "document_name": ticket}
        )
    return mark_read(filters)


def mark_read(filters: dict) -> int:
    unread = frappe.db.count("Notification Log", filters)
    if unread:
        frappe.db.set_value(
            "Notification Log", filters, "read", 1, update_modified=False
        )
        frappe.publish_realtime("indicator_hide", user=frappe.session.user)
    return unread


def notify_ticket_reopened(
    ticket: str, agents: list[str], reopened_by: str | None = None
) -> None:
    """Notify assigned agents that a resolved ticket went back to Open.

    An inbound email is pulled as Administrator, so that caller passes the
    sender as ``reopened_by``; everyone else is the session user.
    """
    if not agents:
        return
    reopened_by = reopened_by or frappe.session.user
    enqueue_create_notification(
        agents,
        {
            "type": "Ticket Reopened",
            "document_type": "HD Ticket",
            "document_name": ticket,
            "subject": _("{0} reopened ticket #{1}").format(
                get_fullname(reopened_by), ticket
            ),
            "from_user": reopened_by,
            "app": HELPDESK_APP,
        },
    )


def notify_new_ticket(ticket: str, created_by: str | None = None) -> None:
    """Notify every active agent who can open a new ticket.

    Checking each agent's access costs queries per agent, so it runs in a job
    instead of holding up the request or email pull that created the ticket.
    """
    frappe.enqueue(
        "helpdesk.notifications.make_new_ticket_notifications",
        ticket=ticket,
        created_by=created_by,
        now=frappe.in_test,
        enqueue_after_commit=not frappe.in_test,
    )


def make_new_ticket_notifications(ticket: str, created_by: str | None = None) -> None:
    # the ticket can be deleted before the job runs
    if not frappe.db.exists("HD Ticket", ticket):
        return
    doc = frappe.get_doc("HD Ticket", ticket)
    # get_all: the job runs as the ticket's creator, often a customer or Guest
    agents = frappe.get_all("HD Agent", filters={"is_active": 1}, pluck="name")
    recipients = [
        agent
        for agent in agents
        if frappe.has_permission("HD Ticket", "read", doc=doc, user=agent)
    ]
    if not recipients:
        return
    make_notification_logs(
        frappe._dict(
            type="New Ticket",
            document_type="HD Ticket",
            document_name=ticket,
            subject=_("New ticket #{0}").format(ticket),
            # the panel renders it as HTML; core sanitizes it on insert
            description=doc.subject,
            from_user=created_by,
            app=HELPDESK_APP,
        ),
        recipients,
    )
