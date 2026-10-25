import frappe


def execute():
    """Backfill ticket source from the dropped via_customer_portal column."""
    Ticket = frappe.qb.DocType("HD Ticket")
    # the column outlives its field until trim-tables
    if frappe.db.has_column("HD Ticket", "via_customer_portal"):
        frappe.qb.update(Ticket).set(Ticket.source, "Portal").where(
            Ticket.via_customer_portal == 1
        ).run()
    # adding the column already defaulted every row to Email; this catches any gap
    frappe.qb.update(Ticket).set(Ticket.source, "Email").where(
        Ticket.source.isnull() | (Ticket.source == "")
    ).run()
