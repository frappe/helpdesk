import frappe
from pypika import Criterion
from helpdesk.utils import is_agent, get_customer

QBActivity = frappe.qb.DocType("HD Ticket Activity")
QBComment = frappe.qb.DocType("HD Ticket Comment")
QBCommunication = frappe.qb.DocType("Communication")
QBContact = frappe.qb.DocType("Contact")
QBCustomField = frappe.qb.DocType("HD Ticket Custom Field")
QBTicket = frappe.qb.DocType("HD Ticket")


@frappe.whitelist()
def get_one(name):
	_is_agent = is_agent()

	query = (
		frappe.qb.from_(QBTicket)
		.select(
			QBTicket._assign,
			QBTicket.agent_group,
			QBTicket.contact,
			QBTicket.customer,
			QBTicket.modified,
			QBTicket.name,
			QBTicket.priority,
			QBTicket.raised_by,
			QBTicket.resolution_by,
			QBTicket.response_by,
			QBTicket.status,
			QBTicket.subject,
			QBTicket.ticket_type,
			QBTicket.via_customer_portal,
		)
		.where(QBTicket.name == name)
	)

	if not _is_agent:
		query = query.where(get_customer_criteria())

	ticket = query.run(as_dict=True)[0]
	contact = (
		frappe.qb.from_(QBContact)
		.select(
			QBContact.company_name,
			QBContact.email_id,
			QBContact.full_name,
			QBContact.image,
			QBContact.mobile_no,
			QBContact.name,
			QBContact.phone,
		)
		.where(QBContact.name == ticket.contact)
		.run(as_dict=True)[0]
	)
	comments = (
		frappe.qb.from_(QBComment)
		.select(
			QBComment.commented_by,
			QBComment.content,
			QBComment.creation,
			QBComment.is_pinned,
			QBComment.name,
		)
		.where(QBComment.reference_ticket == name)
		.run(as_dict=True)
	)
	communications = (
		frappe.qb.from_(QBCommunication)
		.select(
			QBCommunication.bcc,
			QBCommunication.cc,
			QBCommunication.content,
			QBCommunication.creation,
			QBCommunication.name,
			QBCommunication.sender,
		)
		.where(QBCommunication.reference_doctype == "HD Ticket")
		.where(QBCommunication.reference_name == name)
		.run(as_dict=True)
	)
	history = (
		frappe.qb.from_(QBActivity)
		.select(
			QBActivity.name, QBActivity.action, QBActivity.owner, QBActivity.creation
		)
		.where(QBActivity.ticket == name)
		.run(as_dict=True)
	)
	custom_fields = (
		frappe.qb.from_(QBCustomField)
		.select(QBCustomField.label, QBCustomField.value, QBCustomField.route)
		.where(QBCustomField.parent == name)
		.where(QBCustomField.parentfield == "custom_fields")
		.where(QBCustomField.parenttype == "HD Ticket")
		.run(as_dict=True)
	)

	return {
		**ticket,
		"comments": comments,
		"communications": communications,
		"contact": contact,
		"history": history,
		"custom_fields": custom_fields,
	}


def get_customer_criteria():
	user = frappe.session.user
	customer = get_customer(user)
	conditions = [
		QBTicket.contact == user,
		QBTicket.customer == customer,
		QBTicket.raised_by == user,
	]
	return Criterion.any(conditions)
