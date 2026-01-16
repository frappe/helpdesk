import frappe


def execute():
    today = frappe.utils.nowdate()
    old_date = frappe.utils.add_days(today, -180)

    BATCH_SIZE = 1000

    # Get tickets in batches
    tickets = frappe.get_list(
        "HD Ticket", filters={"creation": ["between", [old_date, today]]}, pluck="name"
    )
    print("TICKETS:", len(tickets))

    for i in range(0, len(tickets), BATCH_SIZE):
        batch = list(tickets[i : i + BATCH_SIZE])

        # Update last_agent_response for batch
        frappe.db.sql(
            """
				UPDATE `tabHD Ticket` t
				SET 
					t.last_agent_response = (
						SELECT MAX(c.creation)
						FROM `tabCommunication` c
						WHERE c.reference_doctype = 'HD Ticket'
							AND c.reference_name = t.name
							AND c.sent_or_received = 'Sent'
					),
					t.last_customer_response = (
						SELECT MAX(c.creation)
						FROM `tabCommunication` c
						WHERE c.reference_doctype = 'HD Ticket'
							AND c.reference_name = t.name
							AND c.sent_or_received = 'Received'
					)
				WHERE (
					(t.last_agent_response IS NULL)
					OR (t.last_customer_response IS NULL)
				)
				AND t.name IN %(batch)s
			""",
            {"batch": batch},
        )

        frappe.db.commit()
