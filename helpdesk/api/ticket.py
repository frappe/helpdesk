import frappe
from frappe import _
from frappe.utils.file_manager import save_file
import base64
from datetime import datetime

from helpdesk.utils import agent_only


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
@agent_only
def bulk_assign_ticket_to_agent(ticket_ids, agent_id=None):
    if ticket_ids:
        ticket_docs = []
        for ticket_id in ticket_ids:
            ticket_doc = assign_ticket_to_agent(ticket_id, agent_id)
            ticket_docs.append(ticket_doc)
        return ticket_docs


@frappe.whitelist()
def save_record_video(docname, file_data, ticket_id):
    if file_data:
        # Remove data URL header if present
        if ',' in file_data:
            file_data = file_data.split(',')[1]

        content = base64.b64decode(file_data)
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M')

        file_doc = save_file(
            fname=f"ticket({ticket_id})-recorded-{now_str}-.webm",
            content=content,
            dt="Communication",
            dn=docname,
            folder="Home/Helpdesk",
            is_private=1
        )
        frappe.clear_cache()
        return {"file_url": file_doc.file_url, "name": file_doc.name}
    else:
        frappe.throw("Missing file data")
