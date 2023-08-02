from contextlib import suppress

import frappe
from frappe.website.utils import cleanup_page_name


@frappe.whitelist()
def create_new(values, template="Default", attachments=[], via_customer_portal=False):
	ticket_doc = frappe.new_doc("HD Ticket")
	ticket_doc.via_customer_portal = via_customer_portal
	ticket_doc.ticket_type = values.get("ticket_type")

	if "contact" in values:
		contact_name = values["contact"]
		ticket_doc.raised_by = get_contact_email(contact_name)
		ticket_doc.contact = contact_name

	if via_customer_portal:
		if not frappe.db.exists("Contact", {"email_id": frappe.session.user}):
			new_contact_name = create_contact_from_user(frappe.session.user)
			ticket_doc.raised_by = frappe.session.user
			ticket_doc.contact = new_contact_name

	ticket_doc.subject = values["subject"]
	ticket_doc.description = values["description"]
	if "customer" in values:
		ticket_doc.customer = values["customer"]

	ticket_doc.template = template
	template_fields = frappe.get_doc("HD Ticket Template", template).fields
	for field in template_fields:
		if field.fieldname in ["subject", "description"]:
			continue
		if not field.reqd and field.fieldname not in values:
			continue
		if field.reqd and field.fieldname not in values:
			frappe.throw(f"Field {field.label} is required")

		route = None
		legacy_route_template = f"/app/{cleanup_page_name(field.options)}/{values[field.fieldname]}"
		with suppress(Exception):
			route = frappe.safe_eval(field.dynamic_route, None, {"value": values[field.fieldname]})

		ticket_doc.append(
			"custom_fields",
			{
				"label": field.label,
				"fieldname": field.fieldname,
				"value": values[field.fieldname],
				"hide_from_customer": field.hide_from_customer,
				"route": route or legacy_route_template,
			},
		)

	ticket_doc.insert(ignore_permissions=True)
	ticket_doc.create_communication_via_contact(ticket_doc.description, attachments)

	return ticket_doc


def get_contact_email(contact_name):
	email_id = frappe.db.get_value("Contact", contact_name, "email_id")
	if email_id:
		return email_id
	email_id = frappe.db.get_value(
		"Contact Email", {"parent": contact_name}, "email_id"
	)
	if email_id:
		return email_id


def create_contact_from_user(user):
	user_doc = frappe.get_doc("User", user)
	new_contact_doc = frappe.get_doc(
		doctype="Contact",
		email_id=user_doc.email,
		full_name=user_doc.full_name,
		first_name=user_doc.first_name,
		last_name=user_doc.last_name,
		user=user_doc.name,
	)
	new_contact_doc.append(
		"email_ids", {"email_id": user_doc.email, "is_primary": True}
	)
	new_contact_doc.insert(ignore_permissions=True)
	return new_contact_doc.name


def assign_ticket_to_agent(ticket_id, agent_id=None):
	if not ticket_id:
		return

	ticket_doc = frappe.get_doc("HD Ticket", ticket_id)

	if not agent_id:
		# assign to self
		agent_id = frappe.session.user

	if not frappe.db.exists("HD Agent", agent_id):
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
