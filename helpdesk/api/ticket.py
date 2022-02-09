import frappe

# TODO: change the allow_guest tag
@frappe.whitelist(allow_guest=True)
def get_tickets():
    all_tickets = frappe.db.sql("""
        SELECT
            ticket.subject,
            ticket.modified,
            ticket.status,
            ticket.name,
            ticket.ticket_type,
            agent.agent_name as assignee,
            contact.name as contact
        FROM `tabTicket` ticket
        LEFT JOIN `tabContact` contact
        ON ticket.contact = contact.name
        LEFT JOIN `tabAgent` agent
        ON ticket.agent = agent.name
        ORDER BY ticket.modified desc
    """, as_dict=1)
    
    return all_tickets

@frappe.whitelist(allow_guest=True)
def get_ticket(ticket_id):
    print('!!! FETCHING TICKET DETAILS !!!')
    ticket_doc = frappe.get_doc("Ticket", ticket_id)
    return ticket_doc
