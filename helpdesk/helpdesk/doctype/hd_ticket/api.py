import frappe
import math
from frappe import _
from frappe.utils import get_user_info_for_avatar
from frappe.utils.caching import redis_cache
from pypika import Criterion, Order
from datetime import datetime, timedelta

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
	QBContact = frappe.qb.DocType("Contact")
	QBTicket = frappe.qb.DocType("HD Ticket")

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

	return {
		**ticket,
		"assignee": get_assignee(ticket._assign),
		"comments": get_comments(name),
		"communications": get_communications(name),
		"contact": contact,
		"history": get_history(name),
		"tags": get_tags(name),
		"template": get_template(ticket.template or DEFAULT_TICKET_TEMPLATE),
		"views": get_views(name),
		"timeentries": get_time_entries(name),
	}


def get_customer_criteria():
	QBTicket = frappe.qb.DocType("HD Ticket")
	user = frappe.session.user
	conditions = [
		QBTicket.contact == user,
		QBTicket.raised_by == user,
	]
	customer = get_customer(user)
	for c in customer:
		conditions.append(QBTicket.customer == c)
	return Criterion.any(conditions)


def get_assignee(_assign: str):
	j = frappe.parse_json(_assign)
	if not j or len(j) < 1:
		return
	return get_user_info_for_avatar(j.pop())


def get_communications(ticket: str):
	QBCommunication = frappe.qb.DocType("Communication")
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
		.where(QBCommunication.reference_name == ticket)
		.orderby(QBCommunication.creation, order=Order.asc)
		.run(as_dict=True)
	)
	for c in communications:
		c.attachments = get_attachments("Communication", c.name)
		c.user = get_user_info_for_avatar(c.sender)
	return communications


def get_comments(ticket: str):
	if not frappe.has_permission("HD Ticket Comment", "read"):
		return []
	QBComment = frappe.qb.DocType("HD Ticket Comment")
	comments = (
		frappe.qb.from_(QBComment)
		.select(
			QBComment.commented_by,
			QBComment.content,
			QBComment.creation,
			QBComment.is_pinned,
			QBComment.name,
		)
		.where(QBComment.reference_ticket == ticket)
		.orderby(QBComment.creation, order=Order.asc)
		.run(as_dict=True)
	)
	for c in comments:
		c.user = get_user_info_for_avatar(c.commented_by)
	return comments

def get_time_entries(ticket: str):
	QBTimeEntry = frappe.qb.DocType("HD Ticket Time Tracking")
	time_entries = (
		frappe.qb.from_(QBTimeEntry)
		.select(
			QBTimeEntry.name,
			QBTimeEntry.description,
			QBTimeEntry.start_time,
			QBTimeEntry.duration,
			QBTimeEntry.agent,
		)
		.where(QBTimeEntry.ticket_id == ticket)
		.orderby(QBTimeEntry.start_time, order=Order.asc)
		.run(as_dict=True)
	)

	for entry in time_entries:
		user_info = get_user_info_for_avatar(entry["agent"])
		entry["user"] = user_info
		entry["duration_in_minutes"] = math.ceil(entry["duration"] / 60)

	return time_entries

def get_history(ticket: str):
	if not frappe.has_permission("HD Ticket Activity", "read"):
		return []
	QBActivity = frappe.qb.DocType("HD Ticket Activity")
	history = (
		frappe.qb.from_(QBActivity)
		.select(
			QBActivity.name, QBActivity.action, QBActivity.owner, QBActivity.creation
		)
		.where(QBActivity.ticket == ticket)
		.orderby(QBActivity.creation, order=Order.desc)
	)
	history = history.run(as_dict=True)
	for h in history:
		h.user = get_user_info_for_avatar(h.owner)
	return history


def get_views(ticket: str):
	QBViewLog = frappe.qb.DocType("View Log")
	views = (
		frappe.qb.from_(QBViewLog)
		.select(
			QBViewLog.creation,
			QBViewLog.name,
			QBViewLog.viewed_by,
		)
		.where(QBViewLog.reference_doctype == "HD Ticket")
		.where(QBViewLog.reference_name == ticket)
		.orderby(QBViewLog.creation, order=Order.desc)
		.run(as_dict=True)
	)
	for v in views:
		v.user = get_user_info_for_avatar(v.viewed_by)
	return views


def get_tags(ticket: str):
	QBTag = frappe.qb.DocType("Tag Link")
	rows = (
		frappe.qb.from_(QBTag)
		.select(QBTag.tag)
		.where(QBTag.document_type == "HD Ticket")
		.where(QBTag.document_name == ticket)
		.orderby(QBTag.creation, order=Order.asc)
		.run(as_dict=True)
	)
	res = []
	for tag in rows:
		res.append(tag.tag)
	return res


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


@frappe.whitelist()
def create_or_update_time_entry(ticket_id, agent, action, duration=None, name=None, maximum_duration_reached=False, description=None, override_duration=None):
	if not frappe.session.user or frappe.session.user == "Guest":
		frappe.throw(_("You must be logged in to access this resource."), frappe.PermissionError)

	if not ticket_id or not agent or not action:
		frappe.throw(_("Missing required parameters."))

	time_entry = None
	if duration:
		durationsec = duration / 1000
	if name:
		time_entry = frappe.get_doc("HD Ticket Time Tracking", name)
	elif action == 'start':
		existing_entry = frappe.db.exists("HD Ticket Time Tracking", {"ticket": ticket_id, "status": "Running"})
		if existing_entry:
			frappe.throw(_("There is already an active time entry for this ticket."))
		time_entry = frappe.new_doc("HD Ticket Time Tracking")
		time_entry.parent = ticket_id
		time_entry.parenttype = 'HD Ticket'
		time_entry.parentfield = 'time_tracking_table'
		time_entry.ticket_id = ticket_id
		time_entry.agent = agent
		time_entry.start_time = datetime.now()
		time_entry.status = 'Running'
		time_entry.description = 'Time Entry in progress'
		time_entry.duration = 0
		time_entry.insert()
	if time_entry:
		if time_entry.agent != frappe.session.user:
			frappe.throw(_("You can only modify your own time entries."))

		session = None
		if action == 'start' or action == 'resume':
			session = frappe.new_doc("HD Ticket Time Tracking Session")
			session.ticket_time_entry = time_entry.name
			session.session_start = datetime.now()
			session.insert()
			session.save(ignore_permissions=True)
			session.reload()
			time_entry.status = 'Running'

		elif action == 'pause' or action == 'complete':
			latest_session_name = frappe.db.get_value("HD Ticket Time Tracking Session", {"ticket_time_entry": time_entry.name, "owner": agent, "session_end": ["is", "null"]}, "name")
			if latest_session_name:
				session = frappe.get_doc("HD Ticket Time Tracking Session", latest_session_name)
				session.session_end = datetime.now()
				session.save()

		if action == 'pause':
			time_entry.status = 'Paused'
			time_entry.duration = durationsec

		elif action == 'complete':
			time_entry.end_time = datetime.now()
			time_entry.status = 'Completed'
			time_entry.description = description
			if maximum_duration_reached:
				time_entry.maximum_duration_reached = True
			
			customer_id = frappe.db.get_value("HD Ticket", ticket_id, "customer")
			rounding_increment = None
			if customer_id:
				customer_rounding_increment = frappe.db.get_value("HD Customer", customer_id, "time_entry_rounding")
				if customer_rounding_increment is not None:
					rounding_increment = customer_rounding_increment

			if rounding_increment is None:
				rounding_increment = frappe.db.get_single_value("HD Settings", "time_entry_rounding")
				rounding_increment = int(rounding_increment) if rounding_increment and str(rounding_increment).isdigit() else 60
				
			if rounding_increment > 0:
				if override_duration is not None:
					time_entry.duration_override_by_user = 1
				rounded_duration_seconds = math.ceil(durationsec / rounding_increment) * rounding_increment
				time_entry.duration = durationsec
				time_entry.rounded_duration = rounded_duration_seconds
			else:
				if override_duration is not None:
					time_entry.duration_override_by_user = 1
				time_entry.duration = durationsec
				time_entry.rounded_duration = durationsec

		if session and not action == 'complete':
			time_entry.save(ignore_permissions=True)
			time_entry.reload()
			sessions = frappe.get_all("HD Ticket Time Tracking Session", filters={"ticket_time_entry": time_entry.name}, fields=["session_start", "session_end"])
			if sessions:
				total_duration_seconds = sum(
					[(frappe.utils.get_datetime(session["session_end"]) - frappe.utils.get_datetime(session["session_start"])).total_seconds() for session in sessions if session["session_end"]],
					0
				)
				time_entry.duration = total_duration_seconds
			else:
				time_entry.duration = 0
				time_entry.rounded_duration = 0
		
		time_entry.save(ignore_permissions=True)
		frappe.db.commit()

	return time_entry.as_dict() if time_entry else {}


@frappe.whitelist()
def is_time_entry_running(time_entry_id):
	status = frappe.db.get_value("HD Ticket Time Tracking", time_entry_id, "status")
	is_active = status == "Running"

	return {
		'is_active': is_active,
		'status': status
	}


@frappe.whitelist()
def get_time_entries_for_ticket(ticket_id):
	time_entries = frappe.get_all("HD Ticket Time Tracking", filters={"parent": ticket_id, "status": "Completed"}, fields=["start_time", "user", "description", "duration_in_minutes"], order_by="start_time")
	return time_entries


@frappe.whitelist()
def check_unfinished_time_entries(ticket_id):
	time_entries = frappe.db.get_all("HD Ticket Time Tracking", filters = [["parent", "=", ticket_id], ["status", "!=", "Completed"]])
	return True if time_entries else False