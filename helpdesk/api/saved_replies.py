import re

import frappe
from frappe import _

from helpdesk.utils import agent_only


def sanitize_template(template: str) -> str:
    original = template
    # Remove any jinja blocks/expressions containing frappe methods
    template = re.sub(r"\{\{[^}]*\.[^}]*\}\}", "", template)
    # Remove {% %} code block tags
    template = re.sub(r"\{%.*?%\}", "", template, flags=re.DOTALL)
    # Remove {# #} comments in case pasting payload through it
    template = re.sub(r"\{#.*?#\}", "", template, flags=re.DOTALL)
    if template != original:
        frappe.throw(_("Saved reply contains disallowed syntax."))
    return template


@frappe.whitelist()
@agent_only
def get_rendered_saved_reply(ticket_id: str | int, saved_reply_id: str | None = None):
    if not saved_reply_id:
        frappe.throw(_("Please provide saved_reply_id"))
    saved_reply = frappe.get_doc("HD Saved Reply", saved_reply_id).message
    ticket = frappe.get_doc("HD Ticket", ticket_id).as_dict()
    user = frappe.get_doc("User", frappe.session.user).as_dict()
    safe_saved_reply = sanitize_template(saved_reply)
    return frappe.render_template(
        safe_saved_reply, {**ticket, **user}, safe_render=True
    )
