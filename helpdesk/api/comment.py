import frappe
from frappe import _

from helpdesk import notifications
from helpdesk.utils import get_doc_room, publish_event

PRESET_EMOJIS = ["👍", "👎", "❤️", "🎉", "👀", "✅"]


@frappe.whitelist()
def toggle_reaction(comment: str, emoji: str) -> dict | None:
    doc = frappe.get_doc("Comment", comment)
    frappe.has_permission("Comment", "read", doc, throw=True)
    frappe.has_permission("HD Ticket", "write", doc.reference_name, throw=True)

    if not frappe.db.get_single_value("HD Settings", "enable_comment_reactions"):
        return

    if emoji not in PRESET_EMOJIS:
        frappe.throw(
            _("Invalid emoji. Only preset emojis are allowed: {0}").format(
                ", ".join(PRESET_EMOJIS)
            )
        )

    user = frappe.session.user
    author = doc.comment_email or doc.owner
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
            if author != user:
                notifications.notify_reaction(doc, user)
    else:
        doc.append("reactions", {"emoji": emoji, "user": user})
        doc.save(ignore_permissions=True)
        action = "added"
        if author != user:
            notifications.notify_reaction(doc, user)

    publish_event(
        "helpdesk:comment-reaction-update",
        room=get_doc_room("HD Ticket", doc.reference_name),
        data={"comment": comment, "ticket_id": doc.reference_name},
    )

    return {"action": action, "emoji": emoji}


@frappe.whitelist()
def get_reactions(comment: str) -> list[dict]:
    if not frappe.db.get_single_value("HD Settings", "enable_comment_reactions"):
        return []

    doc = frappe.get_doc("Comment", comment)
    frappe.has_permission("Comment", "read", doc, throw=True)
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
            {"user": r.user, "full_name": user_info.full_name or r.user}
        )

        if r.user == current_user:
            reactions_map[r.emoji]["current_user_reacted"] = True

    for emoji in reactions_map:
        reactions_map[emoji]["count"] = len(reactions_map[emoji]["users"])

    return list(reactions_map.values())


@frappe.whitelist()
def get_preset_emojis() -> list[str]:
    return PRESET_EMOJIS
