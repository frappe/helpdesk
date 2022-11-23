import json
import frappe

from frappe.website.utils import cleanup_page_name
from frappedesk.frappedesk.doctype.ticket_activity.ticket_activity import (
	log_ticket_activity,
)
from frappedesk.frappedesk.doctype.ticket.ticket import (
	create_communication_via_contact,
	get_all_conversations,
	create_communication_via_agent,
)
from frappe.desk.form.assign_to import clear as clear_all_assignments
from frappe.utils import datetime

from frappedesk.frappedesk.doctype.sla.sla import get_expected_time_for
from frappe.automation.doctype.assignment_rule.assignment_rule import apply
from frappe.contacts.doctype.contact.contact import get_contact_name


@frappe.whitelist()
def bulk_insert_tickets(tickets, sla="Default"):
	# trying a faster way to insert tickets
	# sla assignement is working
	# communication creation is working
	# base assignment rule is working
	# assignment rule based on agent group is working (TODO: but a bit slow, could be improved by increasing number of dedicated workers)
	# bulk creation of contacts via background job is working (TODO: use bulk insert instead of enqueue, need to figure ot a way to avoid creating duplicate contacts)

	communications = []

	resolution_by_wrt_priority = {}
	response_by_wrt_priority = {}

	if frappe.db.count("Ticket") >= 1:
		ticket_doc = frappe.get_all(
			"Ticket",
			fields=["name", "idx"],
			order_by="idx desc",
			limit_start=0,
			limit_page_length=1,
		)[0]
		t_idx = ticket_doc.idx
		t_name = ticket_doc.name
	else:
		t_idx = 0
		t_name = "0"

	if frappe.db.count("Communication") >= 1:
		communication_doc = frappe.get_all(
			"Communication",
			fields=["name", "idx"],
			order_by="idx desc",
			limit_start=0,
			limit_page_length=1,
		)[0]
		c_idx = communication_doc.idx
		c_name = communication_doc.name
	else:
		c_idx = 0
		c_name = "0"

	priorities = ["Low", "Medium", "High", "Urgent"]
	sla_doc = frappe.get_doc("SLA", sla)
	creation_time = datetime.datetime.now()

	for priority in priorities:
		p = sla_doc.get_sla_priority(priority)
		p.update(
			{
				"support_and_resolution": sla_doc.support_and_resolution,
				"holiday_list": sla_doc.holiday_list,
			}
		)
		response_by = get_expected_time_for(
			parameter="response", service_level=p, start_date_time=creation_time
		)
		resolution_by = get_expected_time_for(
			parameter="resolution", service_level=p, start_date_time=creation_time
		)
		response_by_wrt_priority[priority] = response_by
		resolution_by_wrt_priority[priority] = resolution_by

	for ticket in tickets:
		t_idx = t_idx + 1
		t_name = str(int(t_name) + 1)

		c_idx = c_idx + 1
		c_name = str(int(c_name) + 1)

		ticket += [
			t_idx,
			t_name,  # name	TODO: folow naming series
			sla,
			resolution_by_wrt_priority[ticket[4]],
			resolution_by_wrt_priority[ticket[4]],
			creation_time,  # modified
			creation_time,  # creation
		]

		communication = [
			c_idx,
			c_name,  # name	TODO: folow naming series
			"Communication",
			"Email",
			"Received",
			"Open",
			f"Re: {ticket[0]}",  # subject
			ticket[2],  # sender
			ticket[1],  # content
			"Linked",
			"Ticket",
			t_name,
			creation_time,
			creation_time,
		]
		communications.append(communication)

	frappe.db.bulk_insert(
		"Ticket",
		[
			"subject",
			"description",
			"raised_by",
			"ticket_type",
			"priority",
			"agent_group",
			"idx",
			"name",
			"sla",
			"response_by",
			"resolution_by",
			"modified",
			"creation",
		],
		tickets,
		ignore_duplicates=True,
	)

	frappe.db.bulk_insert(
		"Communication",
		[
			"idx",
			"name",
			"communication_type",
			"communication_medium",
			"sent_or_received",
			"email_status",
			"subject",
			"sender",
			"content",
			"status",
			"reference_doctype",
			"reference_name",
			"modified",
			"creation",
		],
		communications,
		ignore_duplicates=True,
	)
	frappe.db.commit()

	bulk_create_contacts_and_assignments_for_tickets(tickets)
	# ticket_names = [ticket[7] for ticket in tickets]
	# bulk_apply("Ticket", ticket_names)


def bulk_create_contacts_and_assignments_for_tickets(tickets):
	background = len(tickets) > 5
	for ticket in tickets:
		if background:
			frappe.enqueue(
				"frappedesk.api.ticket.create_contacts_and_assignments_for_tickets", ticket=ticket,
			)
		else:
			create_contacts_and_assignments_for_tickets(ticket)


def create_contacts_and_assignments_for_tickets(ticket):
	email = ticket[2]
	contact_name = get_contact_name(email)
	if not contact_name and email:
		email_parts = email.split("@")
		first_name = frappe.unscrub(email_parts[0])

		try:
			contact_name = (
				f"{first_name}-{email_parts[1]}" if first_name == "Contact" else first_name
			)
			contact = frappe.get_doc(
				{"doctype": "Contact", "first_name": contact_name, "name": contact_name}
			)
			contact.add_email(email_id=email, is_primary=True)
			contact.insert(ignore_permissions=True)
			contact_name = contact.name
		except Exception:
			contact.log_error("Unable to add contact")

	frappe.db.set_value("Ticket", ticket[7], "contact", contact_name)
	apply(doctype="Ticket", name=ticket[7])


@frappe.whitelist()
def get_ticket(ticket_id):
	ticket_doc = frappe.get_doc("Ticket", ticket_id)
	ticket_doc = ticket_doc.__dict__
	ticket_doc["assignees"] = get_agent_assigned_to_ticket(ticket_id)
	ticket_doc["contact"] = get_contact(ticket_id)

	return ticket_doc


@frappe.whitelist()
def create_new(values, template="Default", attachments=[], via_customer_portal=False):
	ticket_doc = frappe.new_doc("Ticket")
	ticket_doc.via_customer_portal = via_customer_portal

	if "contact" in values:
		contact_doc = frappe.get_doc("Contact", values["contact"])
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
				user=user_doc.name,
			)
			new_contact_doc.append("email_ids", {"email_id": user_doc.email, "is_primary": True})
			new_contact_doc.insert(ignore_permissions=True)
			ticket_doc.contact = new_contact_doc.name

	ticket_doc.subject = values["subject"]
	ticket_doc.description = values["description"]

	ticket_doc.template = template
	template_fields = frappe.get_doc("Ticket Template", template).fields
	for field in template_fields:
		if field.fieldname in ["subject", "description"]:
			continue
		if field.auto_set and field.auto_set_via == "Backend (Python)":
			continue
		else:
			ticket_doc.append(
				"custom_fields",
				{
					"label": field.label,
					"fieldname": field.fieldname,
					"value": values[field.fieldname],
					"route": f"/app/{cleanup_page_name(field.options)}/{values[field.fieldname]}"
					if field.fieldtype == "Link"
					else "",
					"is_action_field": field.is_action_field,
				},
			)

	ticket_doc.insert(ignore_permissions=True)
	# TODO: remove this if condition after refactoring doctype/ticket.py logic regarding this
	create_communication_via_contact(ticket_doc.name, ticket_doc.description, attachments)
	# if not via_customer_portal:

	return ticket_doc


@frappe.whitelist()
def update_contact(ticket_id, contact):
	def full_name(contact):
		_full_name = ""
		if contact.first_name:
			_full_name += contact.first_name
		if contact.last_name:
			_full_name += " " + contact.last_name
		return _full_name

	if ticket_id:
		ticket_doc = frappe.get_doc("Ticket", ticket_id)
		contact_doc = frappe.get_doc("Contact", contact)
		if contact_doc.email_ids and len(contact_doc.email_ids) > 0:
			ticket_doc.raised_by = contact_doc.email_ids[0].email_id
			ticket_doc.contact = contact_doc.name
			log_ticket_activity(ticket_id, f"contact set to {full_name(contact_doc)}")

		ticket_doc.save()

		return ticket_doc


def get_agent_assigned_to_ticket(ticket_id):
	agents = []
	assignee_list = frappe.db.get_value("Ticket", ticket_id, "_assign")
	if assignee_list:
		assignees = json.loads(assignee_list)
		if len(assignees) > 0:
			agent = frappe.qb.DocType("Agent")
			user = frappe.qb.DocType("User")
			query = (
				frappe.qb.from_(agent)
				.join(user)
				.on(agent.name == user.name)
				.select(agent.name, agent.agent_name)
				.where(agent.name.isin(assignees))
			)
			agents = query.run(as_dict=True)
	return agents


@frappe.whitelist()
def mark_ticket_as_seen(ticket_id):
	if ticket_id:
		return frappe.get_doc("Ticket", ticket_id).add_seen()


@frappe.whitelist()
def assign_ticket_to_agent(ticket_id, agent_id=None):
	if not ticket_id:
		return

	ticket_doc = frappe.get_doc("Ticket", ticket_id)

	if not agent_id:
		# assign to self
		agent_id = frappe.session.user

	if not frappe.db.exists("Agent", agent_id):
		frappe.throw("Tickets can only assigned to agents")

	ticket_doc.assign_agent(agent_id)
	return ticket_doc


@frappe.whitelist()
def bulk_assign_ticket_to_agent(ticket_ids, agent_id=None):
	if ticket_ids:
		ticket_docs = []
		for ticket_id in ticket_ids:
			ticket_doc = assign_ticket_to_agent(ticket_id, agent_id)
			ticket_docs.append(ticket_doc)
		return ticket_docs


@frappe.whitelist()
def assign_ticket_type(ticket_id, type):
	if ticket_id:
		ticket_doc = frappe.get_doc("Ticket", ticket_id)

		if ticket_doc.ticket_type != type:
			ticket_doc.ticket_type = check_and_create_ticket_type(type).name
			ticket_doc.update_priority_based_on_ticket_type()
			ticket_doc.save()
			log_ticket_activity(ticket_id, f"type set to {type}")

		return ticket_doc


@frappe.whitelist()
def assign_ticket_status(ticket_id, status):
	if ticket_id:
		ticket_doc = frappe.get_doc("Ticket", ticket_id)

		if ticket_doc.status != status:
			ticket_doc.status = status
			ticket_doc.save(ignore_permissions=True)
			log_ticket_activity(ticket_id, f"status set to {status}")

		return ticket_doc


@frappe.whitelist()
def set_ticket_notes(ticket_id, notes):
	if ticket_id:
		ticket_doc = frappe.get_doc("Ticket", ticket_id)

		if ticket_doc.notes != notes:
			ticket_doc.notes = notes
			ticket_doc.save()
			log_ticket_activity(ticket_id, f"updated notes")

		return ticket_doc


@frappe.whitelist()
def bulk_assign_ticket_status(ticket_ids, status):
	if ticket_ids:
		ticket_docs = []
		for ticket_id in ticket_ids:
			ticket_doc = assign_ticket_status(ticket_id, status)
			ticket_docs.append(ticket_doc)
		return {"docs": ticket_docs, "status": status}


@frappe.whitelist()
def assign_ticket_priority(ticket_id, priority):
	if ticket_id:
		ticket_doc = frappe.get_doc("Ticket", ticket_id)

		if ticket_doc.priority != priority:
			ticket_doc.priority = priority
			ticket_doc.save()
			log_ticket_activity(ticket_id, f"priority set to {priority}")

		return ticket_doc


@frappe.whitelist()
def assign_ticket_group(ticket_id, agent_group):
	if ticket_id:
		ticket_doc = frappe.get_doc("Ticket", ticket_id)
		if ticket_doc.agent_group != agent_group:
			current_assigned_agent_doc = ticket_doc.get_assigned_agent()
			if (
				(
					current_assigned_agent_doc
					and not current_assigned_agent_doc.in_group(
						agent_group
					)  # if assigned agent is not in the new group
				)
				and frappe.get_doc(
					"Assignment Rule", frappe.get_doc("Agent Group", agent_group).assignment_rule
				).users  # check if there are any users(agnets) in the new group assignment rule
			):
				clear_all_assignments("Ticket", ticket_id)
				# new agent will be assigned automatically via assignment rule

			ticket_doc.agent_group = agent_group
			log_ticket_activity(ticket_id, f"team set to {agent_group}")
			ticket_doc.save()

		return ticket_doc


@frappe.whitelist()
def get_all_ticket_types():
	return frappe.get_all("Ticket Type", pluck="name")


@frappe.whitelist()
def get_all_ticket_statuses():
	statuses = list(frappe.get_meta("Ticket").get_field("status").options.split("\n"))
	return statuses


@frappe.whitelist()
def get_all_ticket_priorities():
	return frappe.get_all("Ticket Priority", pluck="name")


def get_contact(ticket_id):
	contact_id = frappe.get_value("Ticket", ticket_id, "contact")
	if contact_id:
		contact_doc = frappe.get_doc("Contact", contact_id)
		return contact_doc
	else:
		ticket_doc = frappe.get_doc("Ticket", ticket_id)
		if ticket_doc.raised_by:
			ticket_doc.set_contact(ticket_doc.raised_by, True)
			contact_id = frappe.get_value("Ticket", ticket_id, "contact")
			if contact_id:
				contact_doc = frappe.get_doc("Contact", contact_id)
				return contact_doc
	return None


@frappe.whitelist()
def get_conversations(ticket_id):
	return get_all_conversations(ticket_id)


@frappe.whitelist()
def submit_conversation_via_agent(ticket_id, message, attachments):
	return create_communication_via_agent(ticket_id, message, attachments)


@frappe.whitelist()
def submit_conversation_via_contact(ticket_id, message, attachments):
	return create_communication_via_contact(ticket_id, message, attachments)


@frappe.whitelist()
def get_other_tickets_of_contact(ticket_id):
	contact = frappe.get_value("Ticket", ticket_id, "raised_by")
	tickets = frappe.get_all(
		"Ticket",
		filters={
			"raised_by": contact,
			"name": ["!=", ticket_id],
			"status": ["not in", ["Closed", "Resolved"]],
		},
		fields=["name", "subject"],
	)
	return tickets


@frappe.whitelist()
def check_and_create_ticket_type(type):
	if not frappe.db.exists("Ticket Type", type):
		ticket_type_doc = frappe.new_doc("Ticket Type")
		ticket_type_doc.name = ticket_type_doc.description = type
		ticket_type_doc.insert()
	else:
		ticket_type_doc = frappe.get_doc("Ticket Type", type)

	return ticket_type_doc


@frappe.whitelist()
def get_all_ticket_templates():
	templates = frappe.get_all("Ticket Template")
	for index, template in enumerate(templates):
		templates[index] = frappe.get_doc("Ticket Template", template.name).__dict__

	return templates


@frappe.whitelist()
def activities(name):
	activities = frappe.db.sql(
		"""
		SELECT action, creation, owner
		FROM `tabTicket Activity`
		WHERE ticket = %(ticket)s
		ORDER BY creation DESC
	""",
		values={"ticket": name},
		as_dict=1,
	)

	return activities


@frappe.whitelist()
def submit_customer_feedback(ticket_id, satisfaction_rating, feedback_text):
	ticket_doc = frappe.get_doc("Ticket", ticket_id)
	ticket_doc.satisfaction_rating = satisfaction_rating
	ticket_doc.customer_feedback = feedback_text
	ticket_doc.feedback_submitted = True
	ticket_doc.save(ignore_permissions=True)
	return ticket_doc
