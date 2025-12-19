# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from helpdesk.mixins.mentions import HasMentions
from helpdesk.utils import capture_event, get_doc_room, publish_event


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
    if emoji not in PRESET_EMOJIS:
        frappe.throw(
            f"Invalid emoji. Only preset emojis are allowed: {', '.join(PRESET_EMOJIS)}"
        )

    if not frappe.db.exists("HD Ticket Comment", comment):
        frappe.throw("Comment not found")

    user = frappe.session.user
    doc = frappe.get_doc("HD Ticket Comment", comment)

    existing_reaction = None
    for r in doc.reactions:
        if r.user == user:
            existing_reaction = r
            break

    if existing_reaction:
        if existing_reaction.emoji == emoji:
            doc.reactions.remove(existing_reaction)
            doc.save(ignore_permissions=True)
            action = "removed"
        else:
            existing_reaction.emoji = emoji
            doc.save(ignore_permissions=True)
            action = "changed"
            if doc.commented_by != user:
                notify_reaction(doc, emoji, user)
    else:
        doc.append("reactions", {"emoji": emoji, "user": user})
        doc.save(ignore_permissions=True)
        action = "added"
        if doc.commented_by != user:
            notify_reaction(doc, emoji, user)

    room = get_doc_room("HD Ticket", doc.reference_ticket)
    publish_event(
        "helpdesk:comment-reaction-update",
        room=room,
        data={"comment": comment, "ticket_id": doc.reference_ticket},
    )

    return {"action": action, "emoji": emoji}


@frappe.whitelist()
def get_reactions(comment: str):
    if not frappe.db.exists("HD Ticket Comment", comment):
        frappe.throw("Comment not found")

    doc = frappe.get_doc("HD Ticket Comment", comment)
    current_user = frappe.session.user

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

    for emoji in reactions_map:
        reactions_map[emoji]["count"] = len(reactions_map[emoji]["users"])

    return list(reactions_map.values())


def notify_reaction(doc, emoji, user):
    try:
        existing = frappe.db.get_value(
            "HD Notification",
            {
                "reference_comment": doc.name,
                "user_to": doc.commented_by,
                "notification_type": "Reaction",
                "read": 0,
            },
            ["name"],
            as_dict=True,
        )

        if existing:
            reacting_users = set()
            for r in doc.reactions:
                if r.user != doc.commented_by:
                    reacting_users.add(r.user)

            if not reacting_users:
                return

            user_names = []
            for u in list(reacting_users)[:3]:
                user_info = frappe.get_cached_doc("User", u)
                user_names.append(user_info.full_name or u)

            if len(reacting_users) > 3:
                others = len(reacting_users) - 3
                message = f"{', '.join(user_names)} and {others} others reacted on your comment"
            elif len(reacting_users) == 1:
                message = f"reacted with {emoji} on your comment"
            else:
                message = f"{', '.join(user_names[:-1])} and {user_names[-1]} reacted on your comment"

            frappe.db.set_value(
                "HD Notification",
                existing.name,
                {"user_from": user, "message": message},
            )
        else:
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
        pass


@frappe.whitelist()
def get_preset_emojis():
    return PRESET_EMOJIS
