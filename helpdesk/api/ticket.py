import frappe

@frappe.whitelist(allow_guest=True)
def get_tickets():
    tickets = frappe.get_all("Ticket", pluck="name")
    return tickets

@frappe.whitelist(allow_guest=True)
def get_ticket(ticket_id):
    ticket_doc = frappe.get_doc("Ticket", ticket_id)
    if ticket_doc.agent:
        agent_name = frappe.get_value("Agent", ticket_doc.agent, "agent_name")
        ticket_doc = ticket_doc.__dict__
        ticket_doc["assignee"] = agent_name
    return ticket_doc

@frappe.whitelist(allow_guest=True)
def assign_ticket_to_agent(ticket_id, agent_id=None):
    if ticket_id:
        ticket_doc = frappe.get_doc("Ticket", ticket_id)
        ticket_doc.agent = agent_id
        ticket_doc.save()

@frappe.whitelist(allow_guest=True)
def assign_ticket_type(ticket_id, type):
    if ticket_id:
        ticket_doc = frappe.get_doc("Ticket", ticket_id)
        ticket_doc.ticket_type = type
        ticket_doc.save()

@frappe.whitelist(allow_guest=True)
def assign_ticket_status(ticket_id, status):
    if ticket_id:
        ticket_doc = frappe.get_doc("Ticket", ticket_id)
        ticket_doc.status = status
        ticket_doc.save()

@frappe.whitelist(allow_guest=True)
def get_all_ticket_types():
    return frappe.get_all("Ticket Type", pluck="name")

#TODO: the code can be made better
@frappe.whitelist(allow_guest=True)
def get_all_ticket_statuses():
    statuses = []
    ticket_doctype = frappe.get_doc("DocType", "Ticket")
    for field in ticket_doctype.fields:
        doc_field = frappe.get_doc("DocField", field.__dict__["name"])
        if doc_field.label == "Status":
            statuses = doc_field.options.split("\n")
    return statuses