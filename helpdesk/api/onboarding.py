import frappe


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


@frappe.whitelist()
def get_general_category_id():
    """Get the id of the general category"""
    category = frappe.get_all(
        "HD Article Category",
        filters={"category_name": ["=", "General"]},
        pluck="name",
        order_by="creation asc",
        limit=1,
    )
    return category[0] if category else None
