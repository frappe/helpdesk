import frappe


def execute():
    """
    Convert all tickets with Overdue status to Open status.
    Disable the Overdue status in HD Ticket Status.
    """
    try:
        # 1. Get all tickets with status Overdue
        overdue_tickets = frappe.get_all(
            "HD Ticket",
            filters={"status": "Overdue"},
            pluck="name"
        )
        
        if overdue_tickets:
            print(f"Converting {len(overdue_tickets)} overdue tickets to Open status")
            
            # Update all overdue tickets to Open
            for ticket in overdue_tickets:
                frappe.db.set_value(
                    "HD Ticket",
                    ticket,
                    {"status": "Open", "status_category": "Open"},
                    update_modified=False
                )
            
            print(f"Successfully converted {len(overdue_tickets)} tickets to Open status")
        else:
            print("No overdue tickets found")
        
        # 2. Disable the Overdue status if it exists
        if frappe.db.exists("HD Ticket Status", "Overdue"):
            frappe.db.set_value(
                "HD Ticket Status",
                "Overdue",
                "enabled",
                0
            )
            print("Disabled Overdue status in HD Ticket Status")
        
        frappe.db.commit()
        print("Patch completed successfully")
        
    except Exception as e:
        frappe.log_error("Convert Overdue to Open Patch Error", frappe.get_traceback())
        print(f"Error in patch: {str(e)}")
