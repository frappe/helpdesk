import frappe
from frappe import _

from helpdesk.utils import agent_only, is_admin


@frappe.whitelist()
@agent_only
def bulk_reply(ticket_ids: list, message: str, attachments: list | None = None):

    if not ticket_ids:
        return {"sent": [], "failed": []}

    # dedupe but keep the order the agent picked. set() orders by hash, which varies
    # per process, and duplicates would attach the same file to a ticket twice
    ticket_ids = list(dict.fromkeys(ticket_ids))

    # Check every ticket before writing anything, so one ticket the agent cannot
    # reply to does not leave the rest of the batch half done
    tickets = []
    for ticket_id in ticket_ids:
        frappe.has_permission("HD Ticket", "write", doc=ticket_id, throw=True)
        tickets.append(frappe.get_doc("HD Ticket", ticket_id))

    sent = []
    failed = []
    for doc in tickets:
        frappe.db.savepoint("bulk_reply")
        try:
            link_attachments_to_tickets(attachments, [doc.name])
            doc.reply_via_agent(
                message, to=doc.raised_by, attachments=attachments or []
            )
            sent.append(doc.name)
        except Exception as e:
            frappe.db.rollback(save_point="bulk_reply")
            failed.append({"ticket_id": doc.name, "error": str(e)})
            frappe.log_error(
                title=f"Bulk reply failed for ticket {doc.name}",
                message=str(e),
            )

    return {"sent": sent, "failed": failed}


def link_attachments_to_tickets(attachments: list | None, ticket_ids: list):
    if not attachments:
        return
    if not ticket_ids:
        return

    for ticket_id in ticket_ids:
        for attachment in attachments:
            file_doc = frappe.get_doc("File", attachment)
            if frappe.db.exists(
                "File",
                {
                    "file_url": file_doc.file_url,
                    "attached_to_doctype": "HD Ticket",
                    "attached_to_name": ticket_id,
                },
            ):
                continue
            # Preserve existing ownership, including files reused on a retry.
            if file_doc.attached_to_name:
                file_doc = frappe.copy_doc(file_doc)
            file_doc.attached_to_doctype = "HD Ticket"
            file_doc.attached_to_name = ticket_id
            file_doc.save()


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


@frappe.whitelist()
def delete_ticket(name: str):
    if not is_admin():
        frappe.throw(
            msg=_("Only administrators can delete tickets."),
            title=_("Not Allowed"),
            exc=frappe.PermissionError,
        )
    frappe.delete_doc("HD Ticket", name, force=True, ignore_permissions=True)
