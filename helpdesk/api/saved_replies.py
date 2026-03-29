import frappe
from frappe import _
from jinja2.sandbox import SandboxedEnvironment

from helpdesk.utils import agent_only

user_whitelist_fields = [
    "first_name",
    "middle_name",
    "last_name",
    "full_name",
    "email",
    "username",
    "language",
    "time_zone",
]


def render_sandboxed_template(template: str, context: dict) -> str:
    env = SandboxedEnvironment()
    try:
        return env.from_string(template).render(context)
    except Exception as e:
        frappe.throw(_("Failed to render template: {0}").format(str(e)))


@frappe.whitelist()
@agent_only
def get_rendered_saved_reply(ticket_id: str | int, saved_reply_id: str | None = None):
    if not saved_reply_id:
        frappe.throw(_("Please provide saved_reply_id"))
    saved_reply = frappe.get_doc("HD Saved Reply", saved_reply_id).message
    # return only valid fields from HD Ticket
    ticket_fields = frappe.get_meta("HD Ticket").get_valid_columns()
    ticket = frappe.db.get_value("HD Ticket", ticket_id, ticket_fields, as_dict=True)
    user = frappe.db.get_value(
        "User", frappe.session.user, user_whitelist_fields, as_dict=True
    )
    return render_sandboxed_template(saved_reply, {**ticket, **user}, safe_render=True)
