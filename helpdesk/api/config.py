import frappe
from frappe.utils import get_user_date_format, get_user_time_format

from helpdesk.utils import can_read_knowledge_base, is_agent

# What the knowledge base needs to render for a guest
GUEST_FIELDS = [
    "brand_name",
    "brand_logo",
    "public_knowledge_base",
    "allow_anonymous_article_voting",
    "banner_image",
    "banner_preset",
    "banner_title",
    "banner_subtitle",
]
# The portal's ticket and organization pages
USER_FIELDS = [
    "hide_raise_ticket_button",
    "is_feedback_mandatory",
    "allow_customer_managers_to_invite",
    "allow_customer_managers_to_manage_organization",
]
# The desk's ticket workflow
AGENT_FIELDS = [
    "skip_email_workflow",
    "restrict_tickets_by_agent_group",
    "assign_within_team",
    "disable_saved_replies_global_scope",
    "enable_comment_reactions",
]
FOOTER_ROW_FIELDS = ["label", "url", "parent_label", "open_in_new_tab"]


@frappe.whitelist(allow_guest=True)  # nosemgrep
def get_config():
    """Each caller gets only the settings its app reads: guests the knowledge base look,
    signed-in users the portal switches, agents the desk workflow"""
    res = frappe._dict(
        session_user=frappe.session.user,
        is_agent=is_agent(),
        # shows the settings editors; saving still checks HD Settings' permissions
        can_edit_settings=frappe.has_permission("HD Settings", "write"),  # nosemgrep
    )
    fields = GUEST_FIELDS
    if res.session_user != "Guest":
        fields = fields + USER_FIELDS
    if res.is_agent:
        fields = fields + AGENT_FIELDS

    settings = frappe.get_cached_doc("HD Settings")
    res.update({field: settings.get(field) for field in fields})
    res.date_format = get_user_date_format()
    res.time_format = get_user_time_format()

    is_readable = can_read_knowledge_base()
    res.ai_search_enabled = bool(is_readable and settings.enable_ai_search)
    if is_readable:
        res.knowledge_base_form_scripts = frappe.get_all(
            "HD Form Script",
            filters={"enabled": 1, "apply_to_knowledge_base": 1},
            pluck="script",
        )
    res.update(get_footer(settings, is_readable and bool(settings.show_footer)))

    res.favicon = get_favicon()
    return res


def get_footer(settings, is_shown: bool) -> dict:
    """The knowledge base footer; empty while it is off or the reader can't see the knowledge base."""
    if not is_shown:
        return {"show_footer": 0, "footer_items": [], "social_links": []}
    return {
        "show_footer": 1,
        "footer_tagline": settings.footer_tagline,
        "footer_copyright": settings.footer_copyright,
        "footer_items": get_footer_rows(settings.footer_items),
        "social_links": get_footer_rows(settings.social_links),
    }


def get_footer_rows(rows: list) -> list[dict]:
    return [{field: d.get(field) for field in FOOTER_ROW_FIELDS} for d in rows]


def get_favicon() -> str:
    """The desk's favicon, which the Studio portal uses too"""
    return (
        frappe.db.get_single_value("HD Settings", "favicon")
        or frappe.db.get_single_value("Website Settings", "favicon")
        or "/assets/helpdesk/desk/favicon.svg"
    )
