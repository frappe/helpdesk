# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

<<<<<<< HEAD
=======

import frappe
from frappe import _
>>>>>>> 67a753e5 (fix: duplicate mention notification)
from frappe.model.document import Document

from helpdesk.mixins.mentions import HasMentions
from helpdesk.utils import capture_event, get_doc_room, publish_event


class HDTicketComment(HasMentions, Document):
    mentions_field = "content"

    def after_insert(self):
        self.notify_mentions()
        event = "helpdesk:ticket-comment"
        data = {"ticket_id": self.reference_ticket}
        telemetry_event = "ticket_comment_added"

        room = get_doc_room("HD Ticket", self.reference_ticket)
        publish_event(
            event,
            room=room,
            data=data,
        )
        capture_event(telemetry_event)

    def after_delete(self):
        event = "helpdesk:ticket-comment"
        data = {"ticket_id": self.reference_ticket}
        telemetry_event = "ticket_comment_deleted"

        room = get_doc_room("HD Ticket", self.reference_ticket)
        publish_event(event, room=room, data=data)
        capture_event(telemetry_event)
