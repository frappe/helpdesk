import frappe


def execute():
    today = frappe.utils.nowdate()
    old_date = frappe.utils.add_days(today, -180)  # All tickets in the last 180 days
    communications = frappe.get_all(
        "Communication",
        filters=[
            ["reference_doctype", "=", "HD Ticket"],
            ["creation", ">=", old_date],
        ],
        fields=["name", "creation", "sent_or_received", "reference_name"],
        order_by="creation desc",
    )
    if not communications:
        return

    ticket_responses = {}

    for c in communications:
        ticket_id = c.reference_name
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

    # Build VALUES from ticket_responses
    values_rows = []
    for ticket_id, resp in ticket_responses.items():
        cust = (
            frappe.db.escape(str(resp["last_customer_response"]))
            if resp["last_customer_response"]
            else "NULL"
        )
        agent = (
            frappe.db.escape(str(resp["last_agent_response"]))
            if resp["last_agent_response"]
            else "NULL"
        )
        values_rows.append(f"({frappe.db.escape(ticket_id)}, {cust}, {agent})")

    # Bulk update
    if values_rows:
        frappe.db.sql(
            f"""
            INSERT INTO `tabHD Ticket` (name, last_customer_response, last_agent_response)
            VALUES {", ".join(values_rows)}
            ON DUPLICATE KEY UPDATE
                last_customer_response = VALUES(last_customer_response),
                last_agent_response = VALUES(last_agent_response)
        """
        )
        frappe.db.commit()
