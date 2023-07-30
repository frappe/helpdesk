import frappe
from frappe import _
from pypika import Criterion, Order

from helpdesk.utils import get_customer, is_agent

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

	try:
		ticket = query.run(as_dict=True)[0]
	except:
		frappe.throw(_("Ticket not found"), frappe.DoesNotExistError)

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
		.orderby(QBComment.creation, order=Order.asc)
		.where(QBComment.reference_ticket == name)
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
		.orderby(QBCommunication.creation, order=Order.asc)
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
		"communications": communications,
		"contact": contact,
		"custom_fields": custom_fields,
		"comments": comments.run(as_dict=True) if _is_agent else [],
		"history": history.run(as_dict=True) if _is_agent else [],
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
