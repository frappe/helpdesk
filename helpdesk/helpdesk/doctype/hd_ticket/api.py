import frappe
from frappe import _
from frappe.utils.caching import redis_cache
from pypika import Criterion, Order

from helpdesk.consts import DEFAULT_TICKET_TEMPLATE
from helpdesk.helpdesk.doctype.hd_ticket_template.api import get_one as get_template
from helpdesk.utils import check_permissions, get_customer, is_agent


@frappe.whitelist()
def new(doc, attachments=[]):
	doc["doctype"] = "HD Ticket"
	doc["via_customer_portal"] = bool(frappe.session.user)
	d = frappe.get_doc(doc).insert()
	d.create_communication_via_contact(d.description, attachments)
	return d


@frappe.whitelist()
def get_one(name):
	check_permissions("HD Ticket", None)
	QBActivity = frappe.qb.DocType("HD Ticket Activity")
	QBComment = frappe.qb.DocType("HD Ticket Comment")
	QBCommunication = frappe.qb.DocType("Communication")
	QBContact = frappe.qb.DocType("Contact")
	QBFeedback = frappe.qb.DocType("HD Ticket Feedback Option")
	QBTicket = frappe.qb.DocType("HD Ticket")
	QBViewLog = frappe.qb.DocType("View Log")

	_is_agent = is_agent()

	query = (
		frappe.qb.from_(QBTicket)
		.select(QBTicket.star)
		.where(QBTicket.name == name)
		.limit(1)
	)

	if not _is_agent:
		query = query.where(get_customer_criteria())

	ticket = query.run(as_dict=True)
	if not len(ticket):
		frappe.throw(_("Ticket not found"), frappe.DoesNotExistError)
	ticket = ticket.pop()

	contact = (
		frappe.qb.from_(QBContact)
		.select(
			QBContact.company_name,
			QBContact.email_id,
			QBContact.image,
			QBContact.mobile_no,
			QBContact.name,
			QBContact.phone,
		)
		.where(QBContact.name == ticket.contact)
		.run(as_dict=True)
	)
	if contact:
		contact = contact[0]

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
		.orderby(QBComment.creation, order=Order.asc)
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
		.orderby(QBCommunication.creation, order=Order.asc)
		.run(as_dict=True)
	)
	feedback = (
		frappe.qb.from_(QBFeedback)
		.select(QBFeedback.name, QBFeedback.label, QBFeedback.rating)
		.where(QBFeedback.name == ticket.feedback)
	)

	for c in communications:
		c.attachments = get_attachments("Communication", c.name)

	history = (
		frappe.qb.from_(QBActivity)
		.select(
			QBActivity.name, QBActivity.action, QBActivity.owner, QBActivity.creation
		)
		.where(QBActivity.ticket == name)
		.orderby(QBActivity.creation, order=Order.desc)
	)
	views = (
		frappe.qb.from_(QBViewLog)
		.select(
			QBViewLog.creation,
			QBViewLog.name,
			QBViewLog.viewed_by,
		)
		.where(QBViewLog.reference_doctype == "HD Ticket")
		.where(QBViewLog.reference_name == name)
		.orderby(QBViewLog.creation, order=Order.desc)
	)

	return {
		**ticket,
		"comments": comments.run(as_dict=True) if _is_agent else [],
		"communications": communications,
		"contact": contact,
		"feedback": feedback.run(as_dict=True).pop() if ticket.feedback else None,
		"history": history.run(as_dict=True) if _is_agent else [],
		"template": get_template(ticket.template or DEFAULT_TICKET_TEMPLATE),
		"views": views.run(as_dict=True) if _is_agent else [],
	}


def get_customer_criteria():
	QBTicket = frappe.qb.DocType("HD Ticket")

	user = frappe.session.user
	customer = get_customer(user)
	conditions = [
		QBTicket.contact == user,
		QBTicket.customer == customer,
		QBTicket.raised_by == user,
	]
	return Criterion.any(conditions)


@redis_cache()
def get_attachments(doctype, name):
	QBFile = frappe.qb.DocType("File")

	return (
		frappe.qb.from_(QBFile)
		.select(QBFile.name, QBFile.file_url, QBFile.file_name)
		.where(QBFile.attached_to_doctype == doctype)
		.where(QBFile.attached_to_name == name)
		.run(as_dict=True)
	)
