import frappe


def execute():
    """Ensure the Overdue HD Ticket Status exists and is enabled."""
    status_name = "Overdue"
    if frappe.db.exists("HD Ticket Status", status_name):
        frappe.db.set_value(
            "HD Ticket Status",
            status_name,
            {"enabled": 1, "category": "Paused"},
        )
        return

    doc = frappe.get_doc(
        {
            "doctype": "HD Ticket Status",
            "label_agent": status_name,
            "label_customer": status_name,
            "category": "Paused",
            "enabled": 1,
        }
    )
    doc.insert(ignore_permissions=True)



