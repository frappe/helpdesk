# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class HDTicketActivity(Document):
	pass


def log_ticket_activity(ticket, action):
	return frappe.get_doc(
		{"doctype": "HD Ticket Activity", "ticket": ticket, "action": action}
	).insert(ignore_permissions=True)
