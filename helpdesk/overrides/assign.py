import frappe
from frappe import _


def validate_agent_availability(doc, method=None):
    
    if doc.reference_type != "HD Ticket":
        return

    assigned_to = doc.allocated_to or doc.owner

    if not assigned_to:
        return

    status = frappe.db.get_value(
        "HD Agent",
        {"user": assigned_to},
        "availability_status",
    )

    if status == "Away":
        frappe.throw(
            msg=_("This agent is marked as Away and cannot be assigned tickets."),
            title=_("Agent Unavailable"),
            exc=frappe.ValidationError,
        )


def validate_hd_ticket_agent(doc, method=None):
    allocated_to = getattr(doc, "allocated_to", None)

    if not allocated_to:
        return

    status = frappe.db.get_value(
        "HD Agent",
        {"user": doc.allocated_to},
        "availability_status",
    )

    if status == "Away":
        frappe.throw(
            msg=_("This agent is marked as Away and cannot be assigned tickets."),
            title=_("Agent Unavailable"),
            exc=frappe.ValidationError,
        )