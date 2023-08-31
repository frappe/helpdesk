# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

from frappe.model.document import Document

from helpdesk.mixins.mentions import HasMentions
from helpdesk.utils import capture_event, publish_event


class HDTicketComment(HasMentions, Document):
	mentions_field = "content"

	def on_update(self):
		self.notify_mentions()

	def after_insert(self):
		event = "helpdesk:new-ticket-comment"
		data = {"ticket_id": self.reference_ticket}
		telemetry_event = "ticket_comment_added"

		publish_event(event, data)
		capture_event(telemetry_event)

	def after_delete(self):
		event = "helpdesk:delete-ticket-comment"
		data = {"ticket_id": self.reference_ticket}
		telemetry_event = "ticket_comment_deleted"

		publish_event(event, data)
		capture_event(telemetry_event)
