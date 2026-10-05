from urllib.parse import urlparse

import frappe
from frappe.utils import get_user_date_format, get_user_time_format

from helpdesk.utils import is_agent

# A header link to one of these shows as its icon, as on Frappe Wiki.
SERVICE_ICONS = {
    "github.com": "github",
    "youtube.com": "youtube",
    "twitter.com": "x",
    "x.com": "x",
    "linkedin.com": "linkedin",
    "discord.com": "discord",
    "discord.gg": "discord",
    "slack.com": "slack",
    "facebook.com": "facebook",
    "instagram.com": "instagram",
    "reddit.com": "reddit",
}


@frappe.whitelist(allow_guest=True)  # nosemgrep
def get_config():
    fields = [
        "brand_name",
        "brand_logo",
        "favicon",
        "public_knowledge_base",
        "prefer_knowledge_base",
        "allow_anonymous_article_voting",
        "banner_image",
        "banner_preset",
        "setup_complete",
        "skip_email_workflow",
        "is_feedback_mandatory",
        "confirm_resolution_after_days",
        "restrict_tickets_by_agent_group",
        "assign_within_team",
        "disable_saved_replies_global_scope",
        "enable_comment_reactions",
        "allow_anyone_to_create_tickets",
    ]
    # A Single omits fields never set; every requested key is answered so the portal reads null.
    values = (
        frappe.get_value(doctype="HD Settings", fieldname=fields, as_dict=True) or {}
    )
    res = frappe._dict({field: values.get(field) for field in fields})

    # The Studio portal has no boot payload, so this also names the session user.
    res.session_user = frappe.session.user
    res.is_agent = is_agent()
    # The same roles the desk's settings tabs check, so the portal can link to the ones this agent sees.
    roles = frappe.get_roles()
    res.is_admin = "System Manager" in roles or "Administrator" in roles
    res.is_manager = "Agent Manager" in roles
    res.date_format = get_user_date_format()
    res.time_format = get_user_time_format()

    # The portal header's admin-set links; public, like the branding above.
    res.header_links = frappe.get_all(
        "Top Bar Item",
        filters={"parenttype": "HD Settings", "parentfield": "portal_header_links"},
        fields=["label", "url", "open_in_new_tab"],
        order_by="idx",
    )
    for link in res.header_links:
        link.icon = service_icon(link.url)

    # Form scripts for the knowledge base pages; a private one keeps them from guests.
    if res.public_knowledge_base or res.session_user != "Guest":
        res.kb_form_scripts = frappe.get_all(
            "HD Form Script",
            filters={"enabled": 1, "apply_to_knowledge_base": 1},
            pluck="script",
        )

    res.favicon = (
        res.favicon
        or frappe.db.get_single_value("Website Settings", "favicon")
        or "/assets/helpdesk/desk/favicon.svg"
    )
    return res


def service_icon(url: str) -> str | None:
    """The service a link points to, by its domain or a subdomain of it."""
    host = (urlparse(url).hostname or "").lower()
    for domain, icon in SERVICE_ICONS.items():
        if host == domain or host.endswith("." + domain):
            return icon
    return None
