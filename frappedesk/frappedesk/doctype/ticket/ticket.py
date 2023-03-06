# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import json
from datetime import timedelta

import frappe
from frappe import _
from frappe.core.utils import get_parent_doc
from frappe.database.database import Criterion, Query
from frappe.desk.form.assign_to import add as assign
from frappe.desk.form.assign_to import clear as clear_all_assignments
from frappe.email.inbox import link_communication_to_document
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import date_diff, get_datetime, now_datetime, time_diff_in_seconds
from frappe.utils.user import is_website_user

from frappedesk.frappedesk.doctype.ticket_activity.ticket_activity import (
	log_ticket_activity,
)


class Ticket(Document):
	@staticmethod
	def get_list_query(query: Query):
		query = Ticket.filter_by_team(query)
		return query

	@staticmethod
	def filter_by_team(query: Query):
		user = frappe.session.user

		if Ticket.can_ignore_restrictions(user):
			return query

		should_filter: str = (
			frappe.get_value(
				"Frappe Desk Settings", None, "restrict_tickets_by_agent_group"
			)
			or "0"
		)

		if not int(should_filter):
			return query

		QBTicket = frappe.qb.DocType("Ticket")
		filters = {"user": user}
		teams = frappe.get_list("Agent Group", filters=filters)
		criterions = [QBTicket.agent_group == team.name for team in teams]

		# Consider tickets without any assigned agent group
		filter_unassigned: str = (
			frappe.get_value(
				"Frappe Desk Settings",
				None,
				"do_not_restrict_tickets_without_an_agent_group",
			)
			or "0"
		)

		if not int(filter_unassigned):
			criterions.append(QBTicket.agent_group.isnull())

		query = query.where(Criterion.any(criterions))

		return query

	@staticmethod
	def can_ignore_restrictions(user: str) -> bool:
		"""
		Check if a user can ignore restrictions. Can be used for admins

		:param user: The user to check against
		:return: Whether the user can ignore restrictions
		"""
		# Get teams which can ignore restrictions, where user is a member
		filters = {"user": user, "ignore_restrictions": True}
		teams = frappe.get_list("Agent Group", filters=filters)

		# Must be part of at-least one team which can ignore restrictions
		return len(teams) > 0

	def autoname(self):
		return self.name

	def get_feed(self):
		return "{0}: {1}".format(_(self.status), self.subject)

	def validate(self):
		if not self.raised_by:
			self.raised_by = frappe.session.user

		self.set_contact(self.raised_by)

	def before_insert(self):
		self.verify_ticket_type()
		self.update_priority_based_on_ticket_type()

	def after_insert(self):
		log_ticket_activity(self.name, "created")

	def on_update(self):
		self.handle_ticket_activity_update()
		self.remove_assignment_if_not_in_team()

	def handle_ticket_activity_update(self):
		"""
		Handles the ticket activity update.
		Should be called inside on_update
		"""
		field_maps = {
			"status": "status",
			"priority": "priority",
			"agent_group": "team",
			"ticket_type": "type",
			"contact": "contact",
		}
		for field in [
			"status",
			"priority",
			"agent_group",
			"contact",
			"ticket_type",
		]:
			if self.has_value_changed(field):
				log_ticket_activity(
					self.name, f"{field_maps[field]} set to {self.as_dict()[field]}"
				)

	def remove_assignment_if_not_in_team(self):
		"""
		Removes the assignment if the agent is not in the team.
		Should be called inside on_update
		"""
		if self.has_value_changed("agent_group") and self.status == "Open":
			current_assigned_agent_doc = self.get_assigned_agent()
			if (
				current_assigned_agent_doc
				and not current_assigned_agent_doc.in_group(self.agent_group)
			) and frappe.get_doc(
				"Assignment Rule",
				frappe.get_doc("Agent Group", self.agent_group).assignment_rule,
			).users:
				clear_all_assignments("Ticket", self.name)
				frappe.publish_realtime(
					"ticket_assignee_update",
					{"ticket_id": self.name},
					after_commit=True,
				)

	def update_priority_based_on_ticket_type(self):
		if self.ticket_type:
			ticket_type_doc = frappe.get_doc("Ticket Type", self.ticket_type)
			if ticket_type_doc.priority:
				self.priority = ticket_type_doc.priority
				self.save()

	def set_contact(self, email_id, save=False):
		import email.utils

		email_id = email.utils.parseaddr(email_id)[1]
		if email_id:
			if not self.contact:
				contact = frappe.db.get_value("Contact", {"email_id": email_id})
				if contact:
					self.contact = contact
					if save:
						self.save()

	def create_communication(self):
		communication = frappe.new_doc("Communication")
		communication.update(
			{
				"communication_type": "Communication",
				"communication_medium": "Email",
				"sent_or_received": "Received",
				"email_status": "Open",
				"subject": self.subject,
				"sender": self.raised_by,
				"content": self.description,
				"status": "Linked",
				"reference_doctype": "Ticket",
				"reference_name": self.name,
			}
		)
		communication.ignore_permissions = True
		communication.ignore_mandatory = True
		communication.save(ignore_permissions=True)

	@frappe.whitelist()
	def split_ticket(self, subject, communication_id):
		# Bug: Pressing enter doesn't send subject
		from copy import deepcopy

		replicated_ticket = deepcopy(self)
		replicated_ticket.subject = subject
		replicated_ticket.ticket_split_from = self.name
		replicated_ticket.first_response_time = 0
		replicated_ticket.first_responded_on = None
		replicated_ticket.creation = now_datetime()

		# Reset SLA
		if replicated_ticket.sla:
			replicated_ticket.service_level_agreement_creation = now_datetime()
			replicated_ticket.sla = None
			replicated_ticket.agreement_status = "Ongoing"
			replicated_ticket.response_by = None
			replicated_ticket.response_by_variance = None
			replicated_ticket.resolution_by = None
			replicated_ticket.resolution_by_variance = None
			replicated_ticket.reset_ticket_metrics()

		frappe.get_doc(replicated_ticket).insert()

		# Replicate linked Communications
		# TODO: get all communications in timeline before this, and modify them to append them to new doc
		comm_to_split_from = frappe.get_doc("Communication", communication_id)
		communications = frappe.get_all(
			"Communication",
			filters={
				"reference_doctype": "Ticket",
				"reference_name": comm_to_split_from.reference_name,
				"creation": (">=", comm_to_split_from.creation),
			},
		)

		for communication in communications:
			doc = frappe.get_doc("Communication", communication.name)
			doc.reference_name = replicated_ticket.name
			doc.save(ignore_permissions=True)

		frappe.get_doc(
			{
				"doctype": "Comment",
				"comment_type": "Info",
				"reference_doctype": "Ticket",
				"reference_name": replicated_ticket.name,
				"content": (
					" - Split the Ticket from <a href='/app/Form/Ticket/{0}'>{1}</a>".format(
						self.name, frappe.bold(self.name)
					)
				),
			}
		).insert(ignore_permissions=True)

		return replicated_ticket.name

	def reset_ticket_metrics(self):
		self.db_set("resolution_time", None)
		self.db_set("user_resolution_time", None)

	def assign_agent(self, agent):
		if self._assign:
			assignees = json.loads(self._assign)
			for assignee in assignees:
				if agent == assignee:
					# the agent is already set as an assignee
					return

		clear_all_assignments("Ticket", self.name)
		assign({"assign_to": [agent], "doctype": "Ticket", "name": self.name})
		agent_name = frappe.get_value("Agent", agent, "agent_name")
		log_ticket_activity(self.name, f"assigned to {agent_name}")
		frappe.publish_realtime(
			"ticket_assignee_update", {"ticket_id": self.name}, after_commit=True
		)

	def get_assigned_agent(self):
		if self._assign:
			assignees = json.loads(self._assign)
			if len(assignees) > 0:
				agent_doc = frappe.get_doc("Agent", assignees[0])
				return agent_doc
		return None

	def on_trash(self):
		activities = frappe.db.get_all("Ticket Activity", {"Ticket": self.name})
		for activity in activities:
			frappe.db.delete("Ticket Activity", activity)

	def verify_ticket_type(self):
		if self.ticket_type:
			return

		settings = frappe.get_doc("Frappe Desk Settings")
		self.ticket_type = settings.default_ticket_type

		if not settings.is_ticket_type_mandatory:
			return

		if not self.ticket_type:
			frappe.throw(_("Ticket type is mandatory"))


def set_descritption_from_communication(doc, type):
	if doc.reference_doctype == "Ticket":
		ticket_doc = frappe.get_doc("Ticket", doc.reference_name)
		if not ticket_doc.via_customer_portal:
			ticket_doc.description = doc.content


@frappe.whitelist()
def create_communication_via_contact(ticket, message, attachments=[]):
	ticket_doc = frappe.get_doc("Ticket", ticket)

	if ticket_doc.status == "Replied":
		ticket_doc.status = "Open"
		log_ticket_activity(ticket, f"status set to Open")
		ticket_doc.save(ignore_permissions=True)

	communication = frappe.new_doc("Communication")
	communication.update(
		{
			"communication_type": "Communication",
			"communication_medium": "Email",
			"sent_or_received": "Received",
			"email_status": "Open",
			"subject": "Re: " + ticket_doc.subject,
			"sender": ticket_doc.raised_by,
			"content": message,
			"status": "Linked",
			"reference_doctype": "Ticket",
			"reference_name": ticket_doc.name,
		}
	)
	communication.ignore_permissions = True
	communication.ignore_mandatory = True
	communication.save(ignore_permissions=True)

	for attachment in attachments:
		file_doc = frappe.get_doc("File", attachment)
		file_doc.attached_to_name = communication.name
		file_doc.attached_to_doctype = "Communication"
		file_doc.save(ignore_permissions=True)


@frappe.whitelist(allow_guest=True)
def create_communication_via_agent(ticket, message, cc, bcc, attachments=None):
	ticket_doc = frappe.get_doc("Ticket", ticket)
	last_ticket_communication_doc = frappe.get_last_doc(
		"Communication", filters={"reference_name": ["=", ticket_doc.name]}
	)

	sent_email = True  # if not set email will not be sent
	reply_email_account = None

	ticket_email_account = (
		last_ticket_communication_doc.email_account
		if last_ticket_communication_doc
		else None
	)

	default_ticket_outgoing_email_account = frappe.get_value(
		"Email Account",
		[
			["use_imap", "=", 1],
			["IMAP Folder", "append_to", "=", "Ticket"],
			["default_outgoing", "=", 1],
		],
	)
	default_outgoing_email_account = frappe.get_value(
		"Email Account", [["Email Account", "default_outgoing", "=", 1]]
	)

	just_sent_email_notification = False

	# 1 if not via customer portal check if email account is set in ticket doc, else check if default outgoing is available, else throw error
	if not ticket_doc.via_customer_portal:
		if (
			ticket_email_account
			and frappe.get_doc("Email Account", ticket_email_account).enable_outgoing
		):
			reply_email_account = ticket_email_account
		elif default_ticket_outgoing_email_account:
			reply_email_account = default_ticket_outgoing_email_account
		elif default_outgoing_email_account:
			reply_email_account = default_outgoing_email_account
			just_sent_email_notification = True
		else:
			return {
				"status": "error",
				"error_code": "No default outgoing email available",
			}
	else:
		if default_ticket_outgoing_email_account:
			# 2 if via customer portal, check if a default outgoing email with IMAP folder with ticket doctype is present, if so use that
			reply_email_account = default_ticket_outgoing_email_account
		elif default_outgoing_email_account:
			# 3 if not check if default outgoing email is present, if then send the mail but it should say reply on the customer portal (as replying in the email will not trigger ticket updatee on desk)
			reply_email_account = default_outgoing_email_account
			just_sent_email_notification = True
		else:
			# 4 if via customer portal and no default outgoing email is present, throw error
			sent_email = False

	communication = frappe.new_doc("Communication")
	communication.update(
		{
			"communication_type": "Communication",
			"communication_medium": "Email",
			"sent_or_received": "Sent",
			"email_status": "Open",
			"subject": "Re: " + ticket_doc.subject + f" (#{ticket_doc.name})",
			"sender": frappe.session.user,
			"recipients": frappe.get_value("User", "Administrator", "email")
			if ticket_doc.raised_by == "Administrator"
			else ticket_doc.raised_by,
			"cc": cc,
			"bcc": bcc,
			"content": message,
			"status": "Linked",
			"reference_doctype": "Ticket",
			"reference_name": ticket_doc.name,
			"email_account": reply_email_account,
		}
	)
	communication.ignore_permissions = True
	communication.ignore_mandatory = True
	communication.save(ignore_permissions=True)

	_attachments = []

	for attachment in attachments:
		file_doc = frappe.get_doc("File", attachment)
		file_doc.attached_to_name = communication.name
		file_doc.attached_to_doctype = "Communication"
		file_doc.save(ignore_permissions=True)

		_attachments.append({"file_url": file_doc.file_url})

	if sent_email:
		reply_to_email = frappe.get_doc("Email Account", reply_email_account).email_id
		try:
			frappe.sendmail(
				subject=f"Re: {ticket_doc.subject}",
				sender=reply_to_email,
				reply_to=reply_to_email,
				recipients=[ticket_doc.raised_by],
				cc=cc,
				bcc=bcc,
				reference_doctype="Ticket",
				reference_name=ticket_doc.name,
				communication=communication.name,
				attachments=_attachments if len(_attachments) > 0 else None,
				template="new_reply_on_customer_portal_notification"
				if just_sent_email_notification
				else None,
				message=message if not just_sent_email_notification else None,
				args={
					"ticket_id": ticket_doc.name,
					"message": message,
					"portal_link": f"{frappe.utils.get_url()}/support/tickets/{ticket_doc.name}",
				}
				if just_sent_email_notification
				else None,
				now=False,
			)
		except:
			frappe.throw(
				"Either setup up support email account or there should be a default"
				" outgoing email account"
			)
	else:
		return {"status": "error", "error_code": "No default outgoing email available"}
	return {
		"status": "success",
	}


@frappe.whitelist()
def update_ticket_status_via_customer_portal(ticket, new_status):
	ticket_doc = frappe.get_doc("Ticket", ticket)

	ticket_doc.status = new_status
	ticket_doc.save(ignore_permissions=True)

	return ticket_doc.status


@frappe.whitelist()
def get_all_conversations(ticket):
	conversations = frappe.db.get_all(
		"Communication",
		filters={"reference_doctype": ["=", "Ticket"], "reference_name": ["=", ticket]},
		order_by="creation asc",
		fields=[
			"name",
			"content",
			"creation",
			"sent_or_received",
			"sender",
			"cc",
			"bcc",
		],
	)

	for conversation in conversations:
		if frappe.db.exists("Agent", conversation.sender):
			# user User details instead of Contact if the sender is an agent
			sender = frappe.get_doc("User", conversation.sender).__dict__
			sender["image"] = sender["user_image"]
		else:
			contacts = frappe.get_all(
				"Contact Email",
				filters=[["email_id", "like", "%{0}".format(conversation.sender)]],
				fields=["parent"],
				limit=1,
			)
			if len(contacts) > 0:
				sender = frappe.get_doc("Contact", contacts[0].parent)
			else:
				sender = frappe.get_last_doc(
					"User", filters={"email": conversation.sender}
				)

		conversation.sender = sender

		attachments = frappe.get_all(
			"File",
			["file_name", "file_url"],
			{
				"attached_to_name": conversation.name,
				"attached_to_doctype": "Communication",
			},
		)

		conversation.attachments = attachments
	return conversations


@frappe.whitelist()
def get_all_attachments(ticket):
	attachments = frappe.get_all(
		"File",
		["file_name", "file_url"],
		{"attached_to_name": ticket, "attached_to_doctype": "Ticket"},
	)
	return attachments


def get_list_context(context=None):
	return {
		"title": _("Tickets"),
		"get_list": get_ticket_list,
		"row_template": "templates/includes/ticket_row.html",
		"show_sidebar": True,
		"show_search": True,
		"no_breadcrumbs": True,
	}


@frappe.whitelist()
def get_user_tickets(filters="{}", order_by="creation desc", impersonate=None):
	print(
		f"CALL: get_user_tickets, filters: {filters} order_by: {order_by} impersonate:"
		f" {impersonate}"
	)
	filters = json.loads(filters)
	filters["raised_by"] = ["=", frappe.session.user]

	if impersonate and frappe.db.exists("Agent", frappe.session.user):
		filters["raised_by"] = ["=", impersonate]

	tickets = frappe.get_all(
		"Ticket",
		filters=filters,
		order_by=order_by,
		fields=[
			"name",
			"subject",
			"description",
			"status",
			"creation",
			"feedback_submitted",
			"satisfaction_rating",
			"customer_feedback",
		],
	)
	return tickets


def get_ticket_list(
	doctype, txt, filters, limit_start, limit_page_length=20, order_by=None
):
	from frappe.www.list import get_list

	user = frappe.session.user
	contact = frappe.db.get_value("Contact", {"user": user}, "name")

	ignore_permissions = False
	if is_website_user():
		if not filters:
			filters = {}

		if contact:
			filters["contact"] = contact
		else:
			filters["raised_by"] = user

		ignore_permissions = True

	return get_list(
		doctype,
		txt,
		filters,
		limit_start,
		limit_page_length,
		ignore_permissions=ignore_permissions,
	)


@frappe.whitelist()
def set_multiple_status(names, status):

	for name in json.loads(names):
		frappe.db.set_value("Ticket", name, "status", status)


@frappe.whitelist()
def set_status(name, status):
	frappe.db.set_value("Ticket", name, "status", status)


def auto_close_tickets():
	"""Auto-close replied support tickets after 7 days"""
	auto_close_after_days = (
		frappe.db.get_value(
			"Frappe Desk Settings", "Frappe Desk Settings", "close_ticket_after_days"
		)
		or 7
	)

	tickets = frappe.db.sql(
		""" select name from tabTicket where status='Replied' and
		modified<DATE_SUB(CURDATE(), INTERVAL %s DAY) """,
		(auto_close_after_days),
		as_dict=True,
	)

	for ticket in tickets:
		doc = frappe.get_doc("Ticket", ticket.get("name"))
		doc.status = "Closed"
		doc.flags.ignore_permissions = True
		doc.flags.ignore_mandatory = True
		doc.save()


def has_website_permission(doc, ptype, user, verbose=False):
	# TODO: the commented code was used earilier, we dont need customers so just commented these out for now.
	# but will need to see if some more logic needs to be added here.
	# from erpnext.controllers.website_list_for_contact import has_website_permission
	# permission_based_on_customer = has_website_permission(doc, ptype, user, verbose)

	# return permission_based_on_customer or doc.raised_by==user
	return doc.raised_by == user


def update_ticket(contact, method):
	"""
	Called when Contact is deleted
	"""
	QBTicket = frappe.qb.DocType("Ticket")
	QBTicket.update().set(QBTicket.contact, "").where(QBTicket.contact == contact.name)


@frappe.whitelist()
def make_task(source_name, target_doc=None):
	return get_mapped_doc(
		"Ticket", source_name, {"Ticket": {"doctype": "Task"}}, target_doc
	)


@frappe.whitelist()
def make_ticket_from_communication(communication, ignore_communication_links=False):
	"""raise a ticket from email"""

	doc = frappe.get_doc("Communication", communication)
	ticket = frappe.get_doc(
		{
			"doctype": "Ticket",
			"subject": doc.subject,
			"communication_medium": doc.communication_medium,
			"raised_by": doc.sender or "",
			"raised_by_phone": doc.phone_no or "",
		}
	).insert(ignore_permissions=True)

	link_communication_to_document(
		doc, "Ticket", ticket.name, ignore_communication_links
	)

	return ticket.name


def get_time_in_timedelta(time):
	"""
	Converts datetime.time(10, 36, 55, 961454) to datetime.timedelta(seconds=38215)
	"""
	return timedelta(hours=time.hour, minutes=time.minute, seconds=time.second)


def set_first_response_time(communication, method):
	if communication.get("reference_doctype") == "Ticket":
		ticket = get_parent_doc(communication)
		if is_first_response(ticket) and ticket.sla:
			first_response_time = calculate_first_response_time(
				ticket, get_datetime(ticket.first_responded_on)
			)
			ticket.db_set("first_response_time", first_response_time)


def is_first_response(ticket):
	responses = frappe.get_all(
		"Communication",
		filters={"reference_name": ticket.name, "sent_or_received": "Sent"},
	)
	if len(responses) == 1:
		return True
	return False


def calculate_first_response_time(ticket, first_responded_on):
	ticket_creation_date = ticket.creation
	ticket_creation_time = get_time_in_seconds(ticket_creation_date)
	first_responded_on_in_seconds = get_time_in_seconds(first_responded_on)
	support_hours = frappe.get_cached_doc("SLA", ticket.sla).support_and_resolution

	if ticket_creation_date.day == first_responded_on.day:
		if is_work_day(ticket_creation_date, support_hours):
			start_time, end_time = get_working_hours(
				ticket_creation_date, support_hours
			)

			# ticket creation and response on the same day during working hours
			if is_during_working_hours(
				ticket_creation_date, support_hours
			) and is_during_working_hours(first_responded_on, support_hours):
				return get_elapsed_time(ticket_creation_date, first_responded_on)

			# ticket creation is during working hours, but first response was after working hours
			elif is_during_working_hours(ticket_creation_date, support_hours):
				return get_elapsed_time(ticket_creation_time, end_time)

			# ticket creation was before working hours but first response is during working hours
			elif is_during_working_hours(first_responded_on, support_hours):
				return get_elapsed_time(start_time, first_responded_on_in_seconds)

			# both ticket creation and first response were after working hours
			else:
				return 1.0  # this should ideally be zero, but it gets reset when the next response is sent if the value is zero

		else:
			return 1.0

	else:
		# response on the next day
		if date_diff(first_responded_on, ticket_creation_date) == 1:
			first_response_time = 0
		else:
			first_response_time = calculate_initial_frt(
				ticket_creation_date,
				date_diff(first_responded_on, ticket_creation_date) - 1,
				support_hours,
			)

		# time taken on day of ticket creation
		if is_work_day(ticket_creation_date, support_hours):
			start_time, end_time = get_working_hours(
				ticket_creation_date, support_hours
			)

			if is_during_working_hours(ticket_creation_date, support_hours):
				first_response_time += get_elapsed_time(ticket_creation_time, end_time)
			elif is_before_working_hours(ticket_creation_date, support_hours):
				first_response_time += get_elapsed_time(start_time, end_time)

		# time taken on day of first response
		if is_work_day(first_responded_on, support_hours):
			start_time, end_time = get_working_hours(first_responded_on, support_hours)

			if is_during_working_hours(first_responded_on, support_hours):
				first_response_time += get_elapsed_time(
					start_time, first_responded_on_in_seconds
				)
			elif not is_before_working_hours(first_responded_on, support_hours):
				first_response_time += get_elapsed_time(start_time, end_time)

		if first_response_time:
			return first_response_time
		else:
			return 1.0


def get_time_in_seconds(date):
	return timedelta(hours=date.hour, minutes=date.minute, seconds=date.second)


def get_working_hours(date, support_hours):
	if is_work_day(date, support_hours):
		weekday = frappe.utils.get_weekday(date)
		for day in support_hours:
			if day.workday == weekday:
				return day.start_time, day.end_time


def is_work_day(date, support_hours):
	weekday = frappe.utils.get_weekday(date)
	for day in support_hours:
		if day.workday == weekday:
			return True
	return False


def is_during_working_hours(date, support_hours):
	start_time, end_time = get_working_hours(date, support_hours)
	time = get_time_in_seconds(date)
	if time >= start_time and time <= end_time:
		return True
	return False


def get_elapsed_time(start_time, end_time):
	return round(time_diff_in_seconds(end_time, start_time), 2)


def calculate_initial_frt(ticket_creation_date, days_in_between, support_hours):
	initial_frt = 0
	for i in range(days_in_between):
		date = ticket_creation_date + timedelta(days=(i + 1))
		if is_work_day(date, support_hours):
			start_time, end_time = get_working_hours(date, support_hours)
			initial_frt += get_elapsed_time(start_time, end_time)

	return initial_frt


def is_before_working_hours(date, support_hours):
	start_time, end_time = get_working_hours(date, support_hours)
	time = get_time_in_seconds(date)
	if time < start_time:
		return True
	return False


def get_holidays(holiday_list_name):
	holiday_list = frappe.get_cached_doc("Service Holiday List", holiday_list_name)
	holidays = [holiday.holiday_date for holiday in holiday_list.holidays]
	return holidays
