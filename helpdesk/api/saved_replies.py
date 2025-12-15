import frappe
from frappe import _

from helpdesk.utils import agent_only


@frappe.whitelist()
@agent_only
def get_rendered_saved_reply(ticket_id, saved_reply_id=None, saved_reply=None):
    if not (saved_reply_id or saved_reply):
        frappe.throw(_("Please provide either saved_reply_id or saved_reply data"))
    if not saved_reply:
        saved_reply = frappe.get_doc("HD Saved Reply", saved_reply_id).message
    ticket = frappe.get_doc("HD Ticket", ticket_id).as_dict()
    user = frappe.get_doc("User", frappe.session.user).as_dict()
    return frappe.render_template(saved_reply, {**ticket, **user})
