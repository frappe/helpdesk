# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.realtime import get_website_room


class HDTicketComment(Document):
	def after_insert(self):
		event = "helpdesk:new-ticket-comment"
		data = {"ticket_id": self.reference_ticket}
		room = get_website_room()

		frappe.publish_realtime(event, message=data, room=room, after_commit=True)

	def after_delete(self):
		event = "helpdesk:delete-ticket-comment"
		data = {"ticket_id": self.reference_ticket}
		room = get_website_room()

		frappe.publish_realtime(event, message=data, room=room, after_commit=True)
