# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and Contributors
# License: AGPLv3. See LICENSE

import frappe
from frappe import _


@frappe.whitelist()
def reply_via_agent(
	ticket_name: int,
	message: str,
	to: str = None,
	cc: str = None,
	bcc: str = None,
	attachments: list = None,
	email_account: str = None,
):
	"""
	Wrapper API to call reply_via_agent method on HD Ticket
	This avoids the run_doc_method signature issue
	"""
	if not ticket_name:
		frappe.throw(_("Ticket name is required"))
	
	ticket = frappe.get_doc("HD Ticket", ticket_name)
	
	# Call the method directly
	return ticket.reply_via_agent(
		message=message,
		to=to,
		cc=cc,
		bcc=bcc,
		attachments=attachments or [],
		email_account=email_account,
	)
