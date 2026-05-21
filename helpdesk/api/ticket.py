import frappe
from frappe import _

from helpdesk.utils import agent_only


@frappe.whitelist()
@agent_only
def bulk_reply(ticket_ids: list, message: str):
    if not ticket_ids:
        return

    ticket_ids = list(set(ticket_ids))  # Remove duplicates

    frappe.enqueue(
        _bulk_reply,
        queue="long",
        ticket_ids=ticket_ids,
        message=message,
    )


def _bulk_reply(ticket_ids: list, message: str):
    for ticket_id in ticket_ids:
        frappe.has_permission("HD Ticket", ticket_id, "write", throw=True)
        doc = frappe.get_doc("HD Ticket", ticket_id)
        try:
            doc.reply_via_agent(message, to=doc.raised_by)
        except Exception as e:
            frappe.log_error(
                title=f"Bulk reply failed for ticket {ticket_id}",
                message=str(e),
            )


def assign_ticket_to_agent(ticket_id, agent_id=None):
    if not ticket_id:
        return

    ticket_doc = frappe.get_doc("HD Ticket", ticket_id)

    if not agent_id:
        # assign to self
        agent_id = frappe.session.user

    if not frappe.db.exists("HD Agent", agent_id):
        frappe.throw(_("Tickets can only be assigned to agents"))

    ticket_doc.assign_agent(agent_id)
    return ticket_doc
