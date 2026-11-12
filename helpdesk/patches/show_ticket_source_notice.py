import frappe


def execute():
    """Tell existing sites' managers that via_customer_portal is now `source`.

    Fresh sites never run this patch, so they never see the notice.
    """
    if frappe.db.count("HD Ticket"):
        frappe.db.set_single_value("HD Settings", "show_ticket_source_notice", 1)
