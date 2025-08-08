# Copyright (c) 2025, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class HDEmailFeedback(Document):
    def validate(self):
        self.validate_key()
        self.validate_existing_feedback()

    def validate_key(self):
        if not self.key:
            frappe.throw(_("Unauthorized access."), title=_("Unauthorized Access"))

        ticket_exists = frappe.db.exists("HD Ticket", {"key": self.key})
        if not ticket_exists:
            frappe.throw(
                _("Ticket does not exist."),
                title=_("Tampered Access"),
            )

    def validate_existing_feedback(self):
        existing_feedback = frappe.db.exists("HD Email Feedback", {"key": self.key})
        if existing_feedback:
            frappe.throw(
                _("You have already provided feedback for this ticket."),
                title=_("Feedback Already Exists"),
            )

    def before_save(self):
        self.attach_feedback_to_ticket()

    def attach_feedback_to_ticket(self):
        ticket_doc = frappe.get_doc("HD Ticket", {"key": self.key})
        if not ticket_doc:
            frappe.throw(
                _("Ticket not found for the provided key."), title=_("Ticket Not Found")
            )
        ticket_doc.feedback_rating = self.feedback_rating
        ticket_doc.feedback_extra = self.feedback_extra
        ticket_doc.status = "Closed"
        ticket_doc.save(ignore_permissions=True)

        self.ticket = ticket_doc.name
