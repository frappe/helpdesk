# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.realtime import get_website_room
from frappe.utils import get_fullname

from helpdesk.utils import extract_mentions


class HDTicketComment(Document):
	def on_change(self):
		mentions = extract_mentions(self.content)

		for mention in mentions:
			values = frappe._dict(
				from_user=self.commented_by,
				to_user=mention.email,
				ticket=self.reference_ticket,
				comment=self.name,
			)

			if frappe.db.exists("HD Notification", values):
				continue

			notification = frappe.get_doc(doctype="HD Notification")
			notification.message = (
				f"{get_fullname(self.owner)} mentioned you in Ticket #{self.reference_ticket}",
			)
			notification.update(values)
			notification.insert(ignore_permissions=True)

	def after_insert(self):
		event = "helpdesk:new-ticket-comment"
		data = {"ticket_id": self.reference_ticket}
		room = get_website_room()

		frappe.publish_realtime(event, message=data, room=room, after_commit=True)
