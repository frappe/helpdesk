# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import append_number_if_name_exists
from frappe.realtime import get_website_room
from frappe.utils.jinja import validate_template

from helpdesk.helpdesk.doctype.hd_ticket.hd_ticket import (
    remove_guest_ticket_creation_permission,
    set_guest_ticket_creation_permission,
)


class HDSettings(Document):
    def validate(self):
        self.validate_auto_close_days()
        self.validate_email_contents()
        self.validate_send_feedback_when_ticket_closed()

    def validate_auto_close_days(self):
        if self.auto_close_tickets and self.auto_close_after_days <= 0:
            frappe.throw(
                _("Day count for auto closing tickets cannot be negative or zero")
            )

    def validate_send_feedback_when_ticket_closed(self):
        if not self.enable_email_ticket_feedback:
            return
        status_category = frappe.db.get_value(
            "HD Ticket Status", self.send_email_feedback_on_status, "category"
        )
        if status_category != "Resolved":
            frappe.throw(
                _(
                    "The status for sending feedback must be of <u>Resolved</u> category."
                )
            )

    def get_base_support_rotation(self):
        """Returns the base support rotation rule if it exists, else creats once and returns it"""

        if not self.base_support_rotation:
            self.create_base_support_rotation()

        return self.base_support_rotation

    def create_base_support_rotation(self):
        """Creates the base support rotation rule, and set it to frappe desk settings"""

        rule_doc = frappe.new_doc("Assignment Rule")
        rule_doc.name = append_number_if_name_exists(
            "Assignment Rule", "Support Rotation"
        )
        rule_doc.document_type = "HD Ticket"
        rule_doc.assign_condition = "status == 'Open'"
        rule_doc.assign_condition_json = '[["status", "==", "Open"]]'
        rule_doc.priority = 0
        rule_doc.disabled = True  # Disable the rule by default, when agents are added to the group, the rule will be enabled

        for day in [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]:
            day_doc = frappe.get_doc({"doctype": "Assignment Rule Day", "day": day})
            rule_doc.append("assignment_days", day_doc)

        rule_doc.save(ignore_permissions=True)
        self.base_support_rotation = rule_doc.name
        self.save(ignore_permissions=True)

        return

    def before_save(self):
        self.update_ticket_permissions()

    def on_update(self):
        event = "helpdesk:settings-updated"
        room = get_website_room()

        frappe.publish_realtime(event, room=room, after_commit=True)

    def update_ticket_permissions(self):
        if self.allow_anyone_to_create_tickets:
            set_guest_ticket_creation_permission()
        if not self.allow_anyone_to_create_tickets:
            remove_guest_ticket_creation_permission()

    def validate_email_contents(self):
        for content_field_name in [
            "feedback_email_content",
            "acknowledgement_email_content",
            "reply_email_to_agent_content",
            "reply_via_agent_email_content",
        ]:
            if not self.has_value_changed(content_field_name):
                continue
            validate_template(getattr(self, content_field_name))

    @property
    def hd_search(self):
        from helpdesk.api.article import search

        return search
