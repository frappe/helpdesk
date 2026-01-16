import frappe


def execute():
    today = frappe.utils.nowdate()
    old_date = frappe.utils.add_days(today, -120)

    Ticket = frappe.qb.DocType("HD Ticket")
    Communication = frappe.qb.DocType("Communication")

    BATCH_SIZE = 1000

    # Get tickets in batches
    tickets = frappe.get_list(
        "HD Ticket",
        filters={"creation": ["between", [old_date, today]]},
        fields=["name"],
        limit_page_length=0,
    )

    for i in range(0, len(tickets), BATCH_SIZE):
        batch = [t["name"] for t in tickets[i : i + BATCH_SIZE]]

        # Update last_agent_response for batch
        (
            frappe.qb.update(Ticket)
            .set(
                Ticket.last_agent_response,
                frappe.qb.from_(Communication)
                .select(frappe.qb.max(Communication.creation))
                .where(
                    (Communication.reference_doctype == "HD Ticket")
                    & (Communication.reference_name == Ticket.name)
                    & (Communication.sent_or_received == "Sent")
                ),
            )
            .where(
                (
                    Ticket.last_agent_response.isnull()
                    | (Ticket.last_agent_response == "")
                )
                & Ticket.name.isin(batch)
            )
        ).run()

        # Update last_customer_response for batch
        (
            frappe.qb.update(Ticket)
            .set(
                Ticket.last_customer_response,
                frappe.qb.from_(Communication)
                .select(frappe.qb.max(Communication.creation))
                .where(
                    (Communication.reference_doctype == "HD Ticket")
                    & (Communication.reference_name == Ticket.name)
                    & (Communication.sent_or_received == "Received")
                ),
            )
            .where(
                (
                    Ticket.last_customer_response.isnull()
                    | (Ticket.last_customer_response == "")
                )
                & Ticket.name.isin(batch)
            )
        ).run()

        frappe.db.commit()
