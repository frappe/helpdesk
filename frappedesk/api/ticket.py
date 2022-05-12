from dataclasses import fields
import frappe
from frappedesk.frappedesk.doctype.ticket.ticket import create_communication_via_contact, get_all_conversations, create_communication_via_agent
from frappe.website.utils import cleanup_page_name
import json

from frappedesk.frappedesk.doctype.ticket_activity.ticket_activity import log_ticket_activity

@frappe.whitelist(allow_guest=True)
def get_tickets():
	all_tickets = frappe.db.sql("""
		SELECT
			ticket.subject,
			ticket.modified,
			ticket.status,
			ticket.name,
			ticket.ticket_type,
			ticket.priority,
			ticket.resolution_by,
			ticket.response_by,
			ticket.agreement_status,
			ticket.contact,
			ticket.template,
			ticket.agent_group,
			ticket.first_responded_on,
			ticket.notes,
			ticket.raised_by
		FROM `tabTicket` ticket
		ORDER BY ticket.creation desc
	""", as_dict=1)

	# TODO: optimize this (try using sql query)
	for ticket in all_tickets:
		assignees = get_agent_assigned_to_ticket(ticket['name'])
		
		ticket['seen'] = frappe.session.user in (frappe.get_value("Ticket", ticket['name'], '_seen') or [])
		ticket['custom_fields'] = frappe.get_doc("Ticket", ticket.name, fields=['custom_fields']).custom_fields
		ticket['assignees'] = assignees
		ticket['contact'] = get_contact(ticket['name'])
	
	return all_tickets

@frappe.whitelist(allow_guest=True)
def get_ticket(ticket_id):
	ticket_doc = frappe.get_doc("Ticket", ticket_id)
	ticket_doc = ticket_doc.__dict__
	ticket_doc['assignees'] = get_agent_assigned_to_ticket(ticket_id)
	ticket_doc['contact'] = get_contact(ticket_id)
	
	return ticket_doc

@frappe.whitelist(allow_guest=True)
def create_new(values, template='Default', attachments=[], via_customer_portal=False):
	ticket_doc = frappe.new_doc("Ticket")
	ticket_doc.via_customer_portal = via_customer_portal

	if 'contact' in values:
		contact_doc = frappe.get_doc("Contact", values['contact'])
		if contact_doc.email_ids and len(contact_doc.email_ids) > 0:
			ticket_doc.raised_by = contact_doc.email_ids[0].email_id
			ticket_doc.contact = contact_doc.name

	if via_customer_portal:
		if not frappe.db.exists({"doctype": "Contact", "email_id": frappe.session.user}):
			user_doc = frappe.get_doc("User", frappe.session.user)
			new_contact_doc = frappe.get_doc(
				doctype="Contact", 
				email_id=user_doc.email,
				full_name=user_doc.full_name,
				first_name=user_doc.first_name,
				last_name=user_doc.last_name,
				user=user_doc.name
			)
			new_contact_doc.append("email_ids", {"email_id": user_doc.email, "is_primary": True})
			new_contact_doc.insert(ignore_permissions=True)
			ticket_doc.contact = new_contact_doc.name

	ticket_doc.subject = values['subject']
	ticket_doc.description = values['description']

	ticket_doc.template = template
	template_fields = frappe.get_doc("Ticket Template", template).fields
	for field in template_fields:
		if field.fieldname in ['subject', 'description']:
			continue
		if not field.auto_set:
			ticket_doc.append('custom_fields', {
				'label': field.label,
				'fieldname': field.fieldname,
				'value': values[field.fieldname],
				'route': f'/app/{cleanup_page_name(field.options)}/{values[field.fieldname]}' if field.fieldtype == 'Link' else ''
			})

	ticket_doc.insert(ignore_permissions=True)
	# TODO: remove this if condition after refactoring doctype/ticket.py logic regarding this
	create_communication_via_contact(ticket_doc.name, ticket_doc.description, attachments)
	# if not via_customer_portal:

	return ticket_doc

@frappe.whitelist(allow_guest=True)
def update_contact(ticket_id, contact):
	if ticket_id:
		ticket_doc = frappe.get_doc("Ticket", ticket_id)
		contact_doc = frappe.get_doc("Contact", contact)
		if contact_doc.email_ids and len(contact_doc.email_ids) > 0:
			ticket_doc.raised_by = contact_doc.email_ids[0].email_id
			ticket_doc.contact = contact_doc.name

		ticket_doc.save()
		
		return ticket_doc

def get_agent_assigned_to_ticket(ticket_id):
	agents = []
	ticket_doc = frappe.get_doc("Ticket", ticket_id)
	if ticket_doc._assign:
		assignees = json.loads(ticket_doc._assign)
		for assignee in assignees:
			if (frappe.db.exists("Agent", assignee)):
				agent = frappe.get_doc("Agent", assignee)
				agent = agent.__dict__
				agent['image'] = frappe.get_value("User", agent["name"], "user_image")
				agents.append(agent)
	return agents

@frappe.whitelist()
def mark_ticket_as_seen(ticket_id):
	if ticket_id:
		return frappe.get_doc("Ticket", ticket_id).add_seen()

@frappe.whitelist(allow_guest=True)
def assign_ticket_to_agent(ticket_id, agent_id=None):
	if ticket_id:
		ticket_doc = frappe.get_doc("Ticket", ticket_id)
		
		if agent_id is None:
			# assign to self
			agent_id = frappe.session.user
			if not frappe.db.exists("Agent", agent_id):
				frappe.throw('Tickets can only assigned to agents')
		
		ticket_doc.assign_agent(agent_id)
		return ticket_doc

@frappe.whitelist(allow_guest=True)
def bulk_assign_ticket_to_agent(ticket_ids, agent_id=None):
	if ticket_ids:
		ticket_docs = []
		for ticket_id in ticket_ids:
			ticket_doc = assign_ticket_to_agent(ticket_id, agent_id)
			ticket_docs.append(ticket_doc)
		return ticket_docs

@frappe.whitelist(allow_guest=True)
def assign_ticket_type(ticket_id, type):
	if ticket_id:
		ticket_doc = frappe.get_doc("Ticket", ticket_id)
		
		if ticket_doc.ticket_type != type:
			ticket_doc.ticket_type = check_and_create_ticket_type(type).name
			ticket_doc.update_priority_based_on_ticket_type()
			ticket_doc.save()
			log_ticket_activity(ticket_id, f"Type set to {type}")

		return ticket_doc

@frappe.whitelist(allow_guest=True)
def assign_ticket_status(ticket_id, status):
	if ticket_id:
		ticket_doc = frappe.get_doc("Ticket", ticket_id)
		
		if ticket_doc.status != status:
			ticket_doc.status = status
			ticket_doc.save(ignore_permissions=True)
			log_ticket_activity(ticket_id, f"Status set to {status}")

		return ticket_doc

@frappe.whitelist(allow_guest=True)
def set_ticket_notes(ticket_id, notes):
	if ticket_id:
		ticket_doc = frappe.get_doc("Ticket", ticket_id)
		
		if ticket_doc.notes != notes:
			ticket_doc.notes = notes
			ticket_doc.save()
			log_ticket_activity(ticket_id, f"Updated notes")

		return ticket_doc


@frappe.whitelist(allow_guest=True)
def bulk_assign_ticket_status(ticket_ids, status):
	if ticket_ids:
		ticket_docs = []
		for ticket_id in ticket_ids:
			ticket_doc = assign_ticket_status(ticket_id, status)
			ticket_docs.append(ticket_doc)
		return ticket_docs

@frappe.whitelist(allow_guest=True)
def assign_ticket_priority(ticket_id, priority):
	if ticket_id:
		ticket_doc = frappe.get_doc("Ticket", ticket_id)
		
		if ticket_doc.priority != priority:
			ticket_doc.priority = priority
			ticket_doc.save()
			log_ticket_activity(ticket_id, f"Priority set to {priority}")

		return ticket_doc

@frappe.whitelist(allow_guest=True)
def assign_ticket_group(ticket_id, agent_group):
	if ticket_id:
		ticket_doc = frappe.get_doc("Ticket", ticket_id)
		
		if ticket_doc.agent_group != agent_group:
			ticket_doc.agent_group = agent_group
			log_ticket_activity(ticket_id, f"Team set to {agent_group}")
			ticket_doc.save()
		
		return ticket_doc

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

@frappe.whitelist(allow_guest=True)
def get_all_ticket_priorities():
	return frappe.get_all("Ticket Priority", pluck="name")

def get_contact(ticket_id):
	contact_id = frappe.get_value("Ticket", ticket_id, "contact")
	if contact_id:
		contact_doc = frappe.get_doc("Contact", contact_id)
		return contact_doc
	else:
		ticket_doc = frappe.get_doc("Ticket", ticket_id)
		if (ticket_doc.raised_by):
			ticket_doc.set_contact(ticket_doc.raised_by, True)
			contact_id = frappe.get_value("Ticket", ticket_id, "contact")
			if (contact_id):
				contact_doc = frappe.get_doc("Contact", contact_id)
				return contact_doc
	return None

@frappe.whitelist(allow_guest=True)
def get_conversations(ticket_id):
	return get_all_conversations(ticket_id)

@frappe.whitelist(allow_guest=True)
def submit_conversation_via_agent(ticket_id, message, attachments):
	return create_communication_via_agent(ticket_id, message, attachments)

@frappe.whitelist(allow_guest=True)
def submit_conversation_via_contact(ticket_id, message, attachments):
	return create_communication_via_contact(ticket_id, message, attachments)

@frappe.whitelist(allow_guest=True)
def get_other_tickets_of_contact(ticket_id):
	contact = frappe.get_value("Ticket", ticket_id, "raised_by")
	tickets = frappe.get_all("Ticket", filters={"raised_by": contact, "name": ["!=", ticket_id], "status": ["not in", ["Closed", "Resolved"]]}, fields=['name', 'subject'])
	return tickets

@frappe.whitelist(allow_guest=True)
def check_and_create_ticket_type(type):
	if not frappe.db.exists("Ticket Type", type):
		ticket_type_doc = frappe.new_doc("Ticket Type")
		ticket_type_doc.name = ticket_type_doc.description = type
		ticket_type_doc.insert()
	else:
		ticket_type_doc = frappe.get_doc("Ticket Type", type)

	return ticket_type_doc

@frappe.whitelist(allow_guest=True)
def get_all_ticket_templates():
	templates = frappe.get_all("Ticket Template")
	for index, template in enumerate(templates):
		templates[index] = frappe.get_doc("Ticket Template", template.name).__dict__
	
	return templates

@frappe.whitelist(allow_guest=True)
def activities(name):
	activities = frappe.db.sql(
		"""
		SELECT action, creation, owner
		FROM `tabTicket Activity`
		WHERE ticket = %(ticket)s
	""",
		values={"ticket": name},
		as_dict=1,
	)

	return activities