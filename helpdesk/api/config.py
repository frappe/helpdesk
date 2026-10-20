import frappe
from frappe.utils import get_user_date_format, get_user_time_format

from helpdesk.utils import is_agent


@frappe.whitelist(allow_guest=True)  # nosemgrep
def get_config():
    fields = [
        "brand_name",
        "brand_logo",
        "public_knowledge_base",
        "allow_anonymous_article_voting",
        "hide_raise_ticket_button",
        "banner_image",
        "banner_preset",
        "setup_complete",
        "skip_email_workflow",
        "is_feedback_mandatory",
        "restrict_tickets_by_agent_group",
        "assign_within_team",
        "disable_saved_replies_global_scope",
        "enable_comment_reactions",
        "allow_customer_managers_to_invite",
        "allow_customer_managers_to_manage_members",
        "allow_customer_managers_to_edit_organization",
        "allow_anyone_to_create_tickets",
    ]
    # A Single omits fields never set; every requested key is answered so the portal reads null.
    values = (
        frappe.get_value(doctype="HD Settings", fieldname=fields, as_dict=True) or {}
    )
    res = frappe._dict({field: values.get(field) for field in fields})

    res.session_user = frappe.session.user
    res.is_agent = is_agent()
    res.can_edit_settings = frappe.has_permission("HD Settings", "write")
    res.date_format = get_user_date_format()
    res.time_format = get_user_time_format()

    # A private knowledge base hides its form scripts from guests.
    if res.public_knowledge_base or res.session_user != "Guest":
        res.knowledge_base_form_scripts = frappe.get_all(
            "HD Form Script",
            filters={"enabled": 1, "apply_to_knowledge_base": 1},
            pluck="script",
        )

    res.favicon = get_favicon()
    return res


def get_favicon() -> str:
    """The desk's favicon, which the Studio portal uses too"""
    return (
        frappe.db.get_single_value("HD Settings", "favicon")
        or frappe.db.get_single_value("Website Settings", "favicon")
        or "/assets/helpdesk/desk/favicon.svg"
    )
