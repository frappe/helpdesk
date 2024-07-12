import json
from email.utils import parseaddr
from functools import lru_cache
from typing import List

import frappe
from frappe import _
from frappe.desk.form.assign_to import add as assign
from frappe.desk.form.assign_to import clear as clear_all_assignments
from frappe.desk.form.assign_to import get as get_assignees
from frappe.model.document import Document
from frappe.query_builder import Case, DocType, Order
from pypika.functions import Count
from pypika.queries import Query
from pypika.terms import Criterion

from helpdesk.consts import DEFAULT_TICKET_PRIORITY, DEFAULT_TICKET_TYPE
from helpdesk.helpdesk.doctype.hd_ticket_activity.hd_ticket_activity import (
	log_ticket_activity,
)
from helpdesk.helpdesk.utils.email import (
	default_outgoing_email_account,
	default_ticket_outgoing_email_account,
)
from helpdesk.search import HelpdeskSearch
from helpdesk.utils import capture_event, get_customer, is_agent, publish_event

from ..hd_notification.utils import clear as clear_notifications
from ..hd_service_level_agreement.utils import get_sla


class HDTicket(Document):

	def before_validate(self):
		self.check_update_perms()
		self.set_ticket_type()

	def check_update_perms(self):
		if self.is_new() or is_agent():
			return
		old_doc = self.get_doc_before_save()
		is_closed = old_doc.status == "Closed"
		is_rated = bool(old_doc.feedback)
		if is_closed or is_rated:
			text = _("Closed or rated tickets cannot be updated by non-agents")
			frappe.throw(text, frappe.PermissionError)

	def set_ticket_type(self):
		pass
def has_permission(doc, user=None):
	return bool(
		doc.contact == user
		or doc.raised_by == user
		or doc.owner == user
		or is_agent(user)
		or doc.customer in get_customer(user)
	)
# Custom perms for list query. Only the `WHERE` part
# https://frappeframework.com/docs/user/en/python-api/hooks#modify-list-query
def permission_query(user):
	user = user or frappe.session.user
	if is_agent(user):
		return
	customer = get_customer(user)
	res = "`tabHD Ticket`.contact={user} OR `tabHD Ticket`.raised_by={user} OR `tabHD Ticket`.owner={user}".format(
		user=frappe.db.escape(user)
	)
	for c in customer:
		res += ' OR `tabHD Ticket`.customer="{customer}"'.format(
			customer=frappe.db.escape(c)
		)
	return res
