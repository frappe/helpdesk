# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import json
from datetime import timedelta

import frappe
from frappe import _
from frappe.core.utils import get_parent_doc
from frappe.email.inbox import link_communication_to_document
from frappe.website.website_generator import WebsiteGenerator
from frappe.model.mapper import get_mapped_doc
from frappe.utils import date_diff, get_datetime, now_datetime, time_diff_in_seconds
from frappe.utils.user import is_website_user


class Ticket(WebsiteGenerator):
	def get_feed(self):
		return "{0}: {1}".format(_(self.status), self.subject)

	def validate(self):
		if self.is_new() and self.via_customer_portal:
			self.flags.create_communication = True

		if not self.raised_by:
			self.raised_by = frappe.session.user

		self.set_contact(self.raised_by)

	def before_save(self):
		self.route = f"support/tickets/{self.name}"

	def on_update(self):
		# Add a communication in the ticket timeline
		if self.flags.create_communication and self.via_customer_portal:
			self.create_communication()
			self.flags.communication_created = None

	def set_contact(self, email_id):
		import email.utils

		email_id = email.utils.parseaddr(email_id)[1]
		if email_id:
			if not self.contact:
				self.contact = frappe.db.get_value("Contact", {"email_id": email_id})

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
		if replicated_ticket.service_level_agreement:
			replicated_ticket.service_level_agreement_creation = now_datetime()
			replicated_ticket.service_level_agreement = None
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
					" - Split the Ticket from <a href='/app/Form/Ticket/{0}'>{1}</a>"
					.format(self.name, frappe.bold(self.name))
				),
			}
		).insert(ignore_permissions=True)

		return replicated_ticket.name

	def reset_ticket_metrics(self):
		self.db_set("resolution_time", None)
		self.db_set("user_resolution_time", None)



@frappe.whitelist()
def create_communication_via_contact(ticket, message, attachments):
	ticket_doc = frappe.get_doc("Ticket", ticket)

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

	if attachments:
		attachments = json.loads(attachments)
		for attachment in attachments:
			file_doc = frappe.get_doc("File", attachment["name"])
			file_doc.attached_to_name = communication.name
			file_doc.attached_to_doctype = "Communication"
			file_doc.save(ignore_permissions=True)

@frappe.whitelist()
def get_all_conversations(ticket):
	conversations = frappe.db.get_all("Communication", filters={"reference_doctype": ["=", "Ticket"], "reference_name": ["=", ticket]}, order_by="creation asc", fields=["name", "content", "creation", "sent_or_received"])
	
	for conversation in conversations:
		attachments = frappe.get_all(
			"File", 
			["file_name", "file_url"],
			{"attached_to_name": conversation.name, "attached_to_doctype": "Communication"}
		)

		conversation.attachments = attachments

	return conversations

@frappe.whitelist()
def get_all_attachments(ticket):
	attachments = frappe.get_all(
		"File",
		["file_name", "file_url"],
		{"attached_to_name": ticket, "attached_to_doctype": "Ticket"}
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
def get_all_user_tickets():
	tickets = frappe.get_all("Ticket", filters={"raised_by": ['=', frappe.session.user]}, fields=['name', 'subject', 'description', 'status', 'creation', 'route'])
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
		frappe.db.get_value("Support Settings", "Support Settings", "close_ticket_after_days")
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
	"""Called when Contact is deleted"""
	frappe.db.sql("""UPDATE `tabTicket` set contact='' where contact=%s""", contact.name)


@frappe.whitelist()
def make_task(source_name, target_doc=None):
	return get_mapped_doc(
		"Ticket", source_name, {"Ticket": {"doctype": "Task"}}, target_doc
	)


@frappe.whitelist()
def make_ticket_from_communication(communication, ignore_communication_links=False):
	""" raise a ticket from email """

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

	link_communication_to_document(doc, "Ticket", ticket.name, ignore_communication_links)

	return ticket.name


def get_time_in_timedelta(time):
	"""
	Converts datetime.time(10, 36, 55, 961454) to datetime.timedelta(seconds=38215)
	"""
	return timedelta(hours=time.hour, minutes=time.minute, seconds=time.second)


def set_first_response_time(communication, method):
	if communication.get("reference_doctype") == "Ticket":
		ticket = get_parent_doc(communication)
		if is_first_response(ticket) and ticket.service_level_agreement:
			first_response_time = calculate_first_response_time(
				ticket, get_datetime(ticket.first_responded_on)
			)
			ticket.db_set("first_response_time", first_response_time)


def is_first_response(ticket):
	responses = frappe.get_all(
		"Communication", filters={"reference_name": ticket.name, "sent_or_received": "Sent"}
	)
	if len(responses) == 1:
		return True
	return False


def calculate_first_response_time(ticket, first_responded_on):
	ticket_creation_date = ticket.creation
	ticket_creation_time = get_time_in_seconds(ticket_creation_date)
	first_responded_on_in_seconds = get_time_in_seconds(first_responded_on)
	support_hours = frappe.get_cached_doc(
		"Service Level Agreement", ticket.service_level_agreement
	).support_and_resolution

	if ticket_creation_date.day == first_responded_on.day:
		if is_work_day(ticket_creation_date, support_hours):
			start_time, end_time = get_working_hours(ticket_creation_date, support_hours)

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
			start_time, end_time = get_working_hours(ticket_creation_date, support_hours)

			if is_during_working_hours(ticket_creation_date, support_hours):
				first_response_time += get_elapsed_time(ticket_creation_time, end_time)
			elif is_before_working_hours(ticket_creation_date, support_hours):
				first_response_time += get_elapsed_time(start_time, end_time)

		# time taken on day of first response
		if is_work_day(first_responded_on, support_hours):
			start_time, end_time = get_working_hours(first_responded_on, support_hours)

			if is_during_working_hours(first_responded_on, support_hours):
				first_response_time += get_elapsed_time(start_time, first_responded_on_in_seconds)
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
	holiday_list = frappe.get_cached_doc("Holiday List", holiday_list_name)
	holidays = [holiday.holiday_date for holiday in holiday_list.holidays]
	return holidays
