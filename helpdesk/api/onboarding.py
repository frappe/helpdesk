import frappe


@frappe.whitelist()
def get_first_sla():
    """Get SLA created by the current user except the default SLA"""
    sla = frappe.get_all(
        "HD Service Level Agreement",
        filters={"name": ["!=", "Default"], "owner": ["=", frappe.session.user]},
        fields=["name"],
        order_by="creation asc",
        limit=1,
    )
    return bool(sla)


@frappe.whitelist()
def get_first_ticket():
    """Get first ticket created except the default ticket"""
    ticket = frappe.get_all(
        "HD Ticket",
        filters={
            "subject": ["!=", "Welcome to Helpdesk"],
            "owner": ["=", frappe.session.user],
        },
        fields=["name"],
        order_by="creation asc",
        limit=1,
    )
    return ticket[0].name if ticket else None
