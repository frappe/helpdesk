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
        ORDER BY ticket.creation desc
    """, as_dict=1)
    
    return all_tickets

@frappe.whitelist(allow_guest=True)
def get_ticket(ticket_id):
    ticket_doc = frappe.get_doc("Ticket", ticket_id)
    return ticket_doc

@frappe.whitelist(allow_guest=True)
def assign_ticket_to_agent(ticket_id, agent_id=None):
    if ticket_id:
        ticket_doc = frappe.get_doc("Ticket", ticket_id)
        ticket_doc.agent = agent_id
        ticket_doc.save()