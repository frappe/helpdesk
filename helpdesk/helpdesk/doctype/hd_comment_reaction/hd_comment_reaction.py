# Copyright (c) 2025, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from helpdesk.utils import capture_event, is_agent, publish_event


class HDCommentReaction(Document):
    def before_insert(self):
        # Check if user already reacted to this comment with the same reaction
        existing = frappe.db.exists(
            "HD Comment Reaction",
            {
                "comment": self.comment,
                "user": self.user,
                "reaction": self.reaction,
            },
        )
        if existing:
            frappe.throw(_("You have already reacted to this comment"))

    def after_insert(self):
        self.notify_comment_author()
        self.publish_reaction_update()
        capture_event("comment_reaction_added")

    def after_delete(self):
        self.publish_reaction_update()
        capture_event("comment_reaction_removed")

    def notify_comment_author(self):
        """Notify the comment author about the reaction"""
        comment = frappe.get_doc("HD Ticket Comment", self.comment)
        
        # Don't notify if user is reacting to their own comment
        if comment.commented_by == self.user:
            return
        
        # Get ticket reference for the notification
        ticket = comment.reference_ticket
        
        frappe.get_doc(
            frappe._dict(
                doctype="HD Notification",
                user_from=self.user,
                user_to=comment.commented_by,
                notification_type="Reaction",
                reference_ticket=ticket,
                reference_comment=self.comment,
                message=f"{frappe.get_value('User', self.user, 'full_name')} reacted {self.reaction} to your comment",
            )
        ).insert(ignore_permissions=True)

    def publish_reaction_update(self):
        """Publish real-time event for reaction updates"""
        comment = frappe.get_doc("HD Ticket Comment", self.comment)
        publish_event(
            "helpdesk:comment-reaction-update",
            {
                "comment_id": self.comment,
                "ticket_id": comment.reference_ticket,
            },
        )


@frappe.whitelist()
def toggle_reaction(comment: str, reaction: str = "👍"):
    """
    Toggle a reaction on a comment. If reaction exists, remove it. Otherwise, add it.
    
    :param comment: Name of the HD Ticket Comment
    :param reaction: Reaction emoji (default: 👍)
    :return: dict with action performed and current reactions
    """
    if not is_agent():
        frappe.throw(_("Only agents can react to comments"), frappe.PermissionError)
    
    user = frappe.session.user
    
    # Check if reaction already exists
    existing = frappe.db.exists(
        "HD Comment Reaction",
        {
            "comment": comment,
            "user": user,
            "reaction": reaction,
        },
    )
    
    if existing:
        # Remove the reaction
        frappe.delete_doc("HD Comment Reaction", existing, ignore_permissions=True)
        action = "removed"
    else:
        # Add the reaction
        doc = frappe.get_doc(
            {
                "doctype": "HD Comment Reaction",
                "comment": comment,
                "user": user,
                "reaction": reaction,
            }
        )
        doc.insert(ignore_permissions=True)
        action = "added"
    
    frappe.db.commit()
    
    return {
        "action": action,
        "reactions": get_comment_reactions(comment),
    }


@frappe.whitelist()
def get_comment_reactions(comment: str):
    """
    Get all reactions for a comment grouped by reaction type.
    
    :param comment: Name of the HD Ticket Comment
    :return: dict with reactions and their users
    """
    reactions = frappe.get_all(
        "HD Comment Reaction",
        filters={"comment": comment},
        fields=["reaction", "user", "name"],
    )
    
    # Group reactions by type
    grouped = {}
    for r in reactions:
        if r.reaction not in grouped:
            grouped[r.reaction] = {
                "count": 0,
                "users": [],
                "current_user_reacted": False,
            }
        
        user_info = frappe.get_value(
            "User", r.user, ["full_name", "user_image"], as_dict=True
        )
        grouped[r.reaction]["count"] += 1
        grouped[r.reaction]["users"].append({
            "user": r.user,
            "full_name": user_info.full_name if user_info else r.user,
            "user_image": user_info.user_image if user_info else None,
        })
        
        if r.user == frappe.session.user:
            grouped[r.reaction]["current_user_reacted"] = True
    
    return grouped
