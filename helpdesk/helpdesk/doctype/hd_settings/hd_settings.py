# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.flow.doctype.flow_knowledge_settings.flow_knowledge_settings import (
    embeddings_configured,
)
from frappe.model.document import Document
from frappe.model.naming import append_number_if_name_exists
from frappe.utils import cint
from frappe.realtime import get_website_room
from frappe.utils.jinja import validate_template

from helpdesk.ai_search import AI_AGENT, AI_MODEL, INSTRUCTIONS, OFF_TOPIC
from helpdesk.api.auth import validate_uploaded_image
from helpdesk.helpdesk.doctype.hd_settings.helpers import (
    sync_brand_to_website_settings,
    sync_home_page_to_website_settings,
)
from helpdesk.helpdesk.doctype.hd_ticket.hd_ticket import (
    remove_guest_ticket_creation_permission,
    set_guest_ticket_creation_permission,
)
from helpdesk.utils import is_safe_link

MAX_FOOTER_COLUMNS = 4


class HDSettings(Document):
    def validate(self):
        self.validate_auto_close_days()
        self.validate_email_contents()
        self.validate_send_feedback_when_ticket_closed()
        self.validate_default_agent_status()
        self.turn_off_guest_home_when_private()
        self.validate_guest_only_settings()
        # every visitor loads it, so a linked image could track them
        validate_uploaded_image(self.banner_image)
        self.validate_footer()
        self.validate_ai_search()

    def validate_ai_search(self):
        self.ai_provider = (self.ai_provider or "").strip().lower()
        self.ai_model = (self.ai_model or "").strip()
        if self.enable_ai_search and not (self.ai_provider and self.ai_model):
            frappe.throw(_("Set a provider and a model to turn on AI search"))
        if cint(self.ai_daily_question_limit) < 1:
            frappe.throw(_("Daily questions per visitor must be at least 1"))

    def validate_footer(self):
        """Footer items mirror Website Settings: column rows without a parent, link rows under one."""
        for d in self.social_links:
            d.parent_label = None
        columns = [d.label for d in self.footer_items if not d.parent_label]
        links = [d for d in self.footer_items if d.parent_label]
        if len(columns) > MAX_FOOTER_COLUMNS:
            frappe.throw(
                _("The footer can have at most {0} link columns").format(
                    MAX_FOOTER_COLUMNS
                )
            )
        if len(set(columns)) < len(columns):
            frappe.throw(_("Each footer column needs a different title"))
        for d in links:
            if d.parent_label not in columns:
                frappe.throw(
                    _("{0}: No footer column is titled {1}").format(
                        frappe.bold(d.label), frappe.bold(d.parent_label)
                    )
                )
        parents = {d.parent_label for d in links}
        for column in columns:
            if column not in parents:
                frappe.throw(
                    _("Footer column {0} needs at least one link").format(
                        frappe.bold(column)
                    )
                )
        for d in links + self.social_links:
            if not is_safe_link(d.url or ""):
                frappe.throw(
                    _("{0}: Start with http://, https://, mailto: or /").format(
                        frappe.bold(d.label or _("Row {0}").format(d.idx))
                    )
                )

    def turn_off_guest_home_when_private(self):
        """A private knowledge base turns away guests, so it can't be their home."""
        if not self.public_knowledge_base and self.has_value_changed(
            "public_knowledge_base"
        ):
            self.knowledge_base_home_page_for_guests = 0

    def validate_guest_only_settings(self):
        """Guests reach only a public knowledge base. Checked only when turned on,
        so a site already in that state still saves its other settings."""
        if self.public_knowledge_base:
            return
        for fieldname in (
            "allow_anonymous_article_voting",
            "knowledge_base_home_page_for_guests",
        ):
            if self.get(fieldname) and self.has_value_changed(fieldname):
                frappe.throw(
                    _("Knowledge base must be public to turn on {0}").format(
                        frappe.bold(_(self.meta.get_label(fieldname)))
                    )
                )

    def validate_default_agent_status(self):
        """The default status should be enabled, else agent creation breaks.
        Empty is handled by the mandatory check."""
        if not self.default_agent_status:
            return

        if frappe.db.get_value("HD Agent Status", self.default_agent_status, "enabled"):
            return

        frappe.throw(_("The default agent status must be enabled."))

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
        if self.has_value_changed("allow_anyone_to_create_tickets"):
            self.update_ticket_permissions()

    def on_update(self):
        sync_brand_to_website_settings(self)
        sync_home_page_to_website_settings(self)
        self.sync_ai_search()

        event = "helpdesk:settings-updated"
        room = get_website_room()

        frappe.publish_realtime(event, room=room, after_commit=True)

    def sync_ai_search(self):
        """Keep the Flow provider, model and agent the assistant runs on in step with this tab."""
        if not self.enable_ai_search:
            return
        self.sync_flow_provider()
        model = self.sync_flow_model()
        self.sync_flow_agent(model)
        self.index_articles_when_turned_on()

    def sync_flow_provider(self):
        """A provider the site already has keeps its own key; the model carries ours."""
        if frappe.db.exists("Flow Provider", self.ai_provider):
            return
        frappe.get_doc({"doctype": "Flow Provider", "provider": self.ai_provider}).insert(
            ignore_permissions=True
        )

    def sync_flow_model(self) -> str:
        model = (
            frappe.get_doc("Flow Model", AI_MODEL)
            if frappe.db.exists("Flow Model", AI_MODEL)
            else frappe.new_doc("Flow Model")
        )
        model.update(
            {"title": AI_MODEL, "provider": self.ai_provider, "model_id": self.ai_model, "enabled": 1}
        )
        if key := self.get_password("ai_api_key", raise_exception=False):
            model.api_key = key
        model.save(ignore_permissions=True)
        return model.name

    def sync_flow_agent(self, model: str):
        from frappe.flow.lib.agent import Agent

        agent = Agent(
            name=AI_AGENT,
            model=model,
            skills=[row.skill for row in self.ai_skills],
            description="Answers knowledge base questions from the articles a reader may see",
            instructions=INSTRUCTIONS.format(
                product=self.brand_name or "Helpdesk", off_topic=OFF_TOPIC
            ),
        )
        agent.sync()
        # sync() keeps an existing agent's model, which a settings change must move
        frappe.db.set_value("Flow Agent", agent.name, "model", model)

    def index_articles_when_turned_on(self):
        if not self.has_value_changed("enable_ai_search"):
            return
        if not embeddings_configured():
            frappe.msgprint(
                _("Set an embedding model in Flow Knowledge Settings to index articles"),
                indicator="orange",
            )
            return
        frappe.enqueue(
            "helpdesk.ai_search.index_all_articles",
            queue="long",
            enqueue_after_commit=True,
        )

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
