import frappe

from helpdesk.utils import is_agent


# Guest-callable by design: it returns only public branding and portal flags, and is_agent is False for guests.
# nosemgrep: frappe-semgrep-rules.rules.security.guest-whitelisted-method
@frappe.whitelist(allow_guest=True)
def get_config():
    fields = [
        "brand_name",
        "brand_logo",
        "favicon",
        "prefer_knowledge_base",
        "setup_complete",
        "skip_email_workflow",
        "is_feedback_mandatory",
        "confirm_resolution_after_days",
        "restrict_tickets_by_agent_group",
        "assign_within_team",
        "disable_saved_replies_global_scope",
        "enable_comment_reactions",
        "show_customer_portal_permission_notice",
    ]
    # A Single omits fields never set; every requested key is answered so the portal reads null.
    values = (
        frappe.get_value(doctype="HD Settings", fieldname=fields, as_dict=True) or {}
    )
    res = frappe._dict({field: values.get(field) for field in fields})

    # The Studio portal has no boot payload, so this also names the session user.
    res.session_user = frappe.session.user
    res.is_agent = is_agent()

    res.favicon = (
        res.favicon
        or frappe.db.get_single_value("Website Settings", "favicon")
        or "/assets/helpdesk/desk/favicon.svg"
    )
    return res
