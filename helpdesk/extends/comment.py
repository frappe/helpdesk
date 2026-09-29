"""Comment permission and lifecycle rules for HD Ticket.

Ticket comments are internal agent notes. Customers can read their own
tickets, so without these they would reach the comments on them too.
"""

import frappe
from frappe import _

from helpdesk.utils import is_admin, is_agent

MAX_PINNED_COMMENTS = 5


def before_insert(doc, method: str | None = None):
    """The insert path ignores permissions, so the write gate has to live here."""
    if doc.reference_doctype != "HD Ticket" or doc.comment_type != "Comment":
        return
    if not is_agent():
        frappe.throw(
            _("You are not permitted to add a comment"), frappe.PermissionError
        )


def validate(doc, method: str | None = None):
    """Caps pinned comments per ticket so the pinned bar stays readable."""
    if doc.reference_doctype != "HD Ticket" or not doc.is_pinned:
        return
    if not doc.has_value_changed("is_pinned"):
        return
    # serialise concurrent pins on this ticket so two requests can't both pass the count
    frappe.db.get_value("HD Ticket", doc.reference_name, "name", for_update=True)
    pinned = frappe.db.count(
        "Comment",
        {
            "reference_doctype": "HD Ticket",
            "reference_name": doc.reference_name,
            "is_pinned": 1,
            "name": ["!=", doc.name],
        },
    )
    if pinned >= MAX_PINNED_COMMENTS:
        frappe.throw(
            _("A ticket can have at most {0} pinned comments").format(
                MAX_PINNED_COMMENTS
            )
        )


def on_trash(doc, method: str | None = None):
    """Core only clears notifications by document, not by source."""
    if doc.reference_doctype != "HD Ticket":
        return
    frappe.db.delete(
        "Notification Log", {"source_doctype": "Comment", "source_name": doc.name}
    )


def has_permission(doc, ptype: str = "read", user: str | None = None) -> bool:
    user = user or frappe.session.user
    # only read: write/delete stay a role question, or no one but Administrator could moderate
    if ptype != "read":
        return True
    if doc.reference_doctype != "HD Ticket":
        return True
    if doc.comment_type in (
        "Assigned",
        "Assignment Completed",
    ) and "Customer" in frappe.get_roles(user):
        return False
    return can_see_ticket_comments(doc.reference_name, user)


def can_see_ticket_comments(ticket: str, user: str | None = None) -> bool:
    """Agents only, and only on a ticket they are allowed to read themselves."""
    user = user or frappe.session.user
    if is_admin(user):
        return True
    if not is_agent(user):
        return False
    return bool(frappe.has_permission("HD Ticket", "read", doc=ticket, user=user))
