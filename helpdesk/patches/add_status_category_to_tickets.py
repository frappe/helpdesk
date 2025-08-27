import frappe


def execute():
    today = frappe.utils.nowdate()
    # 90 days ago
    old_date = frappe.utils.add_days(today, -120)

    Ticket = frappe.qb.DocType("HD Ticket")
    TicketStatus = frappe.qb.DocType("HD Ticket Status")
    q = (
        frappe.qb.update(Ticket)
        .join(TicketStatus)
        .on(Ticket.status == TicketStatus.name)
        .set(Ticket.status_category, TicketStatus.category)
        .where(
            (Ticket.status_category.isnull() | (Ticket.status_category == ""))
            & Ticket.creation.between(old_date, today)
        )
    )
    q.run()
