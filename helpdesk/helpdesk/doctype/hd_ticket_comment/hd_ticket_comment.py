# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from helpdesk.mixins.mentions import HasMentions
from helpdesk.utils import capture_event, get_doc_room, publish_event


# Preset allowed emojis
PRESET_EMOJIS = ["👍", "👎", "❤️", "🎉", "👀", "✅"]


class HDTicketComment(HasMentions, Document):
    mentions_field = "content"

    def on_update(self):
        self.notify_mentions()

    def after_insert(self):
        event = "helpdesk:ticket-comment"
        data = {"ticket_id": self.reference_ticket}
        telemetry_event = "ticket_comment_added"

        room = get_doc_room("HD Ticket", self.reference_ticket)
        publish_event(
            event,
            room=room,
            data=data,
        )
        capture_event(telemetry_event)

    def after_delete(self):
        event = "helpdesk:ticket-comment"
        data = {"ticket_id": self.reference_ticket}
        telemetry_event = "ticket_comment_deleted"

        room = get_doc_room("HD Ticket", self.reference_ticket)
        publish_event(event, room=room, data=data)
        capture_event(telemetry_event)


@frappe.whitelist()
def toggle_reaction(comment: str, emoji: str):
    """Add or remove a reaction on a comment. Only one reaction per user allowed."""
    # Validate emoji is from preset list
    if emoji not in PRESET_EMOJIS:
        frappe.throw(
            f"Invalid emoji. Only preset emojis are allowed: {', '.join(PRESET_EMOJIS)}"
        )

    if not frappe.db.exists("HD Ticket Comment", comment):
        frappe.throw("Comment not found")

    user = frappe.session.user
    doc = frappe.get_doc("HD Ticket Comment", comment)

    # Check if user already has any reaction
    existing_reaction = None
    for r in doc.reactions:
        if r.user == user:
            existing_reaction = r
            break

    if existing_reaction:
        if existing_reaction.emoji == emoji:
            # Remove reaction (toggle off same emoji)
            doc.reactions.remove(existing_reaction)
            doc.save(ignore_permissions=True)
            action = "removed"
        else:
            # Replace with new emoji (one reaction per user)
            existing_reaction.emoji = emoji
            doc.save(ignore_permissions=True)
            action = "changed"

            # Notify comment author
            if doc.commented_by != user:
                notify_reaction(doc, emoji, user)
    else:
        # Add new reaction
        doc.append("reactions", {"emoji": emoji, "user": user})
        doc.save(ignore_permissions=True)
        action = "added"

        # Notify comment author
        if doc.commented_by != user:
            notify_reaction(doc, emoji, user)

    # Publish real-time update
    room = get_doc_room("HD Ticket", doc.reference_ticket)
    publish_event(
        "helpdesk:comment-reaction-update",
        room=room,
        data={"comment": comment, "ticket_id": doc.reference_ticket},
    )

    return {"action": action, "emoji": emoji}


@frappe.whitelist()
def get_reactions(comment: str):
    """Get all reactions for a comment grouped by emoji."""
    if not frappe.db.exists("HD Ticket Comment", comment):
        frappe.throw("Comment not found")

    doc = frappe.get_doc("HD Ticket Comment", comment)
    current_user = frappe.session.user

    # Group reactions by emoji
    reactions_map = {}
    for r in doc.reactions:
        if r.emoji not in reactions_map:
            reactions_map[r.emoji] = {
                "emoji": r.emoji,
                "users": [],
                "current_user_reacted": False,
            }

        user_info = frappe.get_cached_doc("User", r.user)
        reactions_map[r.emoji]["users"].append(
            {
                "user": r.user,
                "full_name": user_info.full_name or r.user,
            }
        )

        if r.user == current_user:
            reactions_map[r.emoji]["current_user_reacted"] = True

    # Add count to each reaction
    for emoji in reactions_map:
        reactions_map[emoji]["count"] = len(reactions_map[emoji]["users"])

    return list(reactions_map.values())


def notify_reaction(doc, emoji, user):
    """Notify comment author about reaction with proper message format."""
    try:
        frappe.get_doc(
            {
                "doctype": "HD Notification",
                "message": f"reacted with {emoji} on your comment",
                "notification_type": "Reaction",
                "reference_comment": doc.name,
                "reference_ticket": doc.reference_ticket,
                "user_from": user,
                "user_to": doc.commented_by,
            }
        ).insert(ignore_permissions=True)
    except Exception:
        pass  # Don't fail if notification fails


@frappe.whitelist()
def get_preset_emojis():
    """Return the list of preset emojis allowed for reactions."""
    return PRESET_EMOJIS
