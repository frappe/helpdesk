import frappe
from frappe import _


def _throw_if_agent_away(user: str):
    
    if not user:
        return
    status = frappe.db.get_value(
        "HD Agent",
        {"user": user},
        "availability_status",
    )
    if status == "Away":
        frappe.throw(
            msg=_("This agent is marked as Away and cannot be assigned tickets."),
            title=_("Agent Unavailable"),
            exc=frappe.ValidationError,
        )



def validate_agent_availability(doc, method=None):
    
    if doc.reference_type != "HD Ticket":
        return
    assigned_to = doc.allocated_to or doc.owner
    _throw_if_agent_away(assigned_to)  

def validate_hd_ticket_agent(doc, method=None):
    
    if not doc.allocated_to:
        return
    if doc.is_new():
        return
    before = doc.get_doc_before_save()
    if before and before.allocated_to == doc.allocated_to:
        return
    _throw_if_agent_away(doc.allocated_to)  