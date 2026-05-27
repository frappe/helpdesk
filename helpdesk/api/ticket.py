import frappe
from frappe import _

from helpdesk.utils import agent_only


@frappe.whitelist()
@agent_only
def bulk_reply(ticket_ids: list, message: str, attachments: list | None = None):

    link_attachments_to_tickets(attachments, ticket_ids)

    if not ticket_ids:
        return

    ticket_ids = list(set(ticket_ids))  # Remove duplicates

    for ticket_id in ticket_ids:
        frappe.has_permission("HD Ticket", "write", doc=ticket_id, throw=True)
        doc = frappe.get_doc("HD Ticket", ticket_id)
        try:
            doc.reply_via_agent(
                message, to=doc.raised_by, attachments=attachments or []
            )
        except Exception as e:
            frappe.log_error(
                title=f"Bulk reply failed for ticket {ticket_id}",
                message=str(e),
            )


def link_attachments_to_tickets(attachments: list | None, ticket_ids: list):
    if not attachments:
        return
    if not ticket_ids:
        return

    # only one attachment is created, but does not refer to any doctype/docname until now. Link it to all the tickets in context.
    # Done as fileuploader only handles for one file, and cant upload to multiple doctypes/docnames at the same time.
    file_doc = frappe.get_doc("File", attachments[0])
    file_doc.attached_to_doctype = "HD Ticket"
    file_doc.attached_to_name = ticket_ids[0]
    file_doc.save()

    for ticket_id in ticket_ids[1:]:
        new_file_doc = frappe.copy_doc(file_doc)
        new_file_doc.attached_to_name = ticket_id
        new_file_doc.insert(ignore_permissions=True)


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
