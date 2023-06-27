import frappe
from frappe.website.utils import cleanup_page_name

from helpdesk.helpdesk.doctype.hd_ticket.hd_ticket import (
	create_communication_via_contact,
)


@frappe.whitelist()
def create_new(values, template="Default", attachments=[], via_customer_portal=False):
	ticket_doc = frappe.new_doc("HD Ticket")
	ticket_doc.via_customer_portal = via_customer_portal
	ticket_doc.ticket_type = values.get("ticket_type")

	if "contact" in values:
		contact_doc = frappe.get_doc("Contact", values["contact"])
		email_id = ""
		if contact_doc.email_id:
			email_id = contact_doc.email_id
		elif contact_doc.email_ids and len(contact_doc.email_ids) > 0:
			email_id = contact_doc.email_ids[0].email_id

		ticket_doc.raised_by = email_id
		ticket_doc.contact = contact_doc.name

	if via_customer_portal:
		if not frappe.db.exists(
			{"doctype": "Contact", "email_id": frappe.session.user}
		):
			user_doc = frappe.get_doc("User", frappe.session.user)
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
			ticket_doc.contact = new_contact_doc.name

	ticket_doc.subject = values["subject"]
	ticket_doc.description = values["description"]
	if "customer" in values:
		ticket_doc.customer = values["customer"]

	ticket_doc.template = template
	template_fields = frappe.get_doc("HD Ticket Template", template).fields
	for field in template_fields:
		if field.fieldname in ["subject", "description"]:
			continue
		if field.auto_set and field.auto_set_via == "Backend (Python)":
			continue
		else:
			if field.fieldname not in values:
				continue
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
	create_communication_via_contact(
		ticket_doc.name, ticket_doc.description, attachments
	)
	# if not via_customer_portal:

	return ticket_doc


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
