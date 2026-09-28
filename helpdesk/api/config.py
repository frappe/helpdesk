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
    # A Single stores only the fields that have been set, so one never touched comes
    # back missing rather than empty — and the portal reads a missing key as undefined
    # instead of as "no value". Every requested field is answered for.
    values = (
        frappe.get_value(doctype="HD Settings", fieldname=fields, as_dict=True) or {}
    )
    res = frappe._dict({field: values.get(field) for field in fields})

    # The only guest-readable endpoint the portals share, so it also answers "who am
    # I?" — the Studio-rendered portal gets no boot payload to read that from.
    res.session_user = frappe.session.user
    # Whether to offer the way back to the agent desk; the desk enforces access itself.
    res.is_agent = is_agent()

    res.favicon = (
        res.favicon
        or frappe.db.get_single_value("Website Settings", "favicon")
        or "/assets/helpdesk/desk/favicon.svg"
    )
    return res
