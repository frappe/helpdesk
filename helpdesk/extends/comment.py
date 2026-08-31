"""Comment permission and lifecycle rules for HD Ticket.

Ticket comments are internal agent notes. Customers can read their own
tickets, so without these they would reach the comments on them too.
"""

import frappe
from frappe import _

from helpdesk.utils import is_admin, is_agent


def before_insert(doc, method: str | None = None):
    """The insert path ignores permissions, so the write gate has to live here."""
    if doc.reference_doctype != "HD Ticket" or doc.comment_type != "Comment":
        return
    if not is_agent():
        frappe.throw(
            _("You are not permitted to add a comment"), frappe.PermissionError
        )


def has_permission(doc, ptype: str = "read", user: str | None = None) -> bool:
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
    if doc.owner == "Administrator" and user != "Administrator":
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
