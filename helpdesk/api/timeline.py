"""Side data for the framework ActivityTimeline: its payload carries neither
comment reactions nor comment attachments, and calls are helpdesk-only rows."""

import frappe
from frappe import _

from helpdesk.helpdesk.doctype.hd_ticket.api import get_attachments, get_call_logs
from helpdesk.utils import is_agent


@frappe.whitelist()
def get_comment_extras(ticket: str) -> dict[str, dict]:
    """One batched call per ticket open: {comment_name: {reactions, attachments}}.
    Re-fetched by the client on helpdesk:comment-reaction-update."""
    ensure_agent_can_read(ticket)
    names = frappe.get_all(
        "Comment",
        filters={
            "reference_doctype": "HD Ticket",
            "reference_name": ticket,
            "comment_type": "Comment",
        },
        pluck="name",
    )
    extras = {name: {"reactions": [], "attachments": []} for name in names}
    if not names:
        return extras
    for name in names:
        extras[name]["attachments"] = get_attachments("Comment", name)
    if frappe.db.get_single_value("HD Settings", "enable_comment_reactions"):
        add_reactions(extras, names)
    return extras


@frappe.whitelist()
def get_ticket_calls(ticket: str) -> list[dict]:
    """Calls merged into the feed as custom rows; loaded on open, no realtime."""
    ensure_agent_can_read(ticket)
    return get_call_logs(ticket)


def ensure_agent_can_read(ticket: str) -> None:
    frappe.has_permission("HD Ticket", "read", ticket, throw=True)
    if not is_agent():
        frappe.throw(_("Not permitted"), frappe.PermissionError)


def add_reactions(extras: dict[str, dict], names: list[str]) -> None:
    """Same shape CommentBox consumed: one entry per emoji with its users."""
    current_user = frappe.session.user
    rows = frappe.get_all(
        "HD Comment Reaction",
        filters={"parenttype": "Comment", "parent": ["in", names]},
        fields=["parent", "emoji", "user"],
    )
    grouped: dict[tuple[str, str], dict] = {}
    for row in rows:
        entry = grouped.setdefault(
            (row.parent, row.emoji),
            {"emoji": row.emoji, "users": [], "current_user_reacted": False},
        )
        entry["users"].append(
            {"user": row.user, "full_name": frappe.utils.get_fullname(row.user)}
        )
        if row.user == current_user:
            entry["current_user_reacted"] = True
    for (parent, _emoji), entry in grouped.items():
        entry["count"] = len(entry["users"])
        extras[parent]["reactions"].append(entry)
