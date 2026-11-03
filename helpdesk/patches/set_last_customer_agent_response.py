import frappe


def execute():
    today = frappe.utils.nowdate()
    old_date = frappe.utils.add_days(today, -180)  # All tickets in the last 180 days
    communications = frappe.get_all(
        "Communication",
        filters=[
            ["reference_doctype", "=", "HD Ticket"],
            ["creation", ">=", old_date],
            ["reference_name", "!=", ""],  # filter out empty strings at DB level
            ["reference_name", "is", "set"],  # filter out NULL values
        ],
        fields=["name", "creation", "sent_or_received", "reference_name"],
        order_by="creation desc",
    )
    if not communications:
        return

    ticket_responses = {}

    for c in communications:
        ticket_id = c.reference_name
        # skip communications without a valid ticket reference (extra safety check)
        if not ticket_id or not str(ticket_id).strip():
            continue
        if ticket_id not in ticket_responses:
            ticket_responses[ticket_id] = {
                "last_customer_response": None,
                "last_agent_response": None,
            }

        # Track latest response by type (communications already sorted by creation desc)
        if (
            c.sent_or_received == "Sent"
            and ticket_responses[ticket_id]["last_agent_response"] is None
        ):
            ticket_responses[ticket_id]["last_agent_response"] = c.creation
        elif (
            c.sent_or_received == "Received"
            and ticket_responses[ticket_id]["last_customer_response"] is None
        ):
            ticket_responses[ticket_id]["last_customer_response"] = c.creation

    frappe.db.bulk_update("HD Ticket", ticket_responses, update_modified=False)
