import json
import uuid
from email.utils import parseaddr
from functools import lru_cache
from typing import List

import frappe
from bs4 import BeautifulSoup
from frappe import _
from frappe.core.page.permission_manager.permission_manager import remove
from frappe.desk.form.assign_to import add as assign
from frappe.desk.form.assign_to import clear as clear_all_assignments
from frappe.desk.form.assign_to import get as get_assignees
from frappe.model.document import Document
from frappe.permissions import add_permission, update_permission_property
from frappe.query_builder import Order
from pypika.functions import Count
from pypika.queries import Query
from pypika.terms import Criterion

from helpdesk.consts import DEFAULT_TICKET_PRIORITY, DEFAULT_TICKET_TYPE
from helpdesk.helpdesk.doctype.hd_settings.helpers import (
    get_default_email_content,
    is_email_content_empty,
)
from helpdesk.helpdesk.doctype.hd_ticket_activity.hd_ticket_activity import (
    log_ticket_activity,
)
from helpdesk.helpdesk.utils.email import (
    default_outgoing_email_account,
    default_ticket_outgoing_email_account,
)
from helpdesk.search import HelpdeskSearch
from helpdesk.utils import (
    capture_event,
    get_agents_team,
    get_customer,
    is_admin,
    is_agent,
    publish_event,
)

from ..hd_notification.utils import clear as clear_notifications
from ..hd_service_level_agreement.utils import get_sla


class HDTicket(Document):
    @property
    def default_open_status(self):
        return frappe.db.get_value(
            "HD Service Level Agreement",
            self.sla,
            "default_ticket_status",
        ) or frappe.db.get_single_value("HD Settings", "default_ticket_status")

    @property
    def ticket_reopen_status(self):
        return frappe.db.get_value(
            "HD Service Level Agreement",
            self.sla,
            "ticket_reopen_status",
        ) or frappe.db.get_single_value("HD Settings", "ticket_reopen_status")

    def publish_update(self):
        publish_event("helpdesk:ticket-update", self.name)
        capture_event("ticket_updated")

    def autoname(self):
        return self.name

    def before_validate(self):
        self.check_update_perms()
        self.set_ticket_type()
        self.set_raised_by()
        self.set_priority()
        self.set_first_responded_on()
        self.set_feedback_values()
        self.set_default_status()
        self.set_status_category()
        # self.apply_escalation_rule()
        self.set_sla()

        self.set_contact()
        self.set_customer()

    def validate(self):
        self.validate_feedback()
        self.validate_ticket_type()

    def before_save(self):
        self.apply_sla()
        if not self.is_new():
            self.handle_ticket_activity_update()

        self.handle_email_feedback()

    def _get_rendered_template(
        self, content: str, default_content: str, args: dict[str, str] | None = None
    ):
        if args is None:
            args = dict()
        template_args = {
            "doc": self.as_dict(),
        }
        for key, value in args.items():
            template_args[key] = value
        return frappe.render_template(
            default_content if is_email_content_empty(content) else content,
            template_args,
        )

    def handle_email_feedback(self):

        if (
            self.is_new()
            or self.via_customer_portal
            or self.feedback_rating
            or not self.has_value_changed("status")
            or not self.key
        ):
            return

        [is_email_feedback_enabled, email_feedback_status] = frappe.get_cached_value(
            "HD Settings",
            "HD Settings",
            ["enable_email_ticket_feedback", "send_email_feedback_on_status"],
        )

        send_feedback_email = int(is_email_feedback_enabled) and (
            email_feedback_status == self.status
            or email_feedback_status == ""
            and self.status == "Closed"
        )

        if not send_feedback_email:
            return

        last_communication = self.get_last_communication()

        url = f"{frappe.utils.get_url()}/ticket-feedback/new?key={self.key}"
        feedback_email_content = frappe.db.get_single_value(
            "HD Settings", "feedback_email_content"
        )
        default_feedback_email_content = get_default_email_content("share_feedback")
        try:
            frappe.sendmail(
                recipients=[self.raised_by],
                subject=f"Re: {self.subject}",
                message=self._get_rendered_template(
                    feedback_email_content,
                    default_feedback_email_content,
                    {"url": url},
                ),
                reference_doctype="HD Ticket",
                reference_name=self.name,
                now=True,
                in_reply_to=last_communication.name if last_communication else None,
                email_headers={"X-Auto-Generated": "hd-email-feedback"},
            )
            frappe.msgprint(_("Feedback email has been sent to the customer"))
        except Exception as e:
            frappe.throw(_("Could not send feedback email,due to: {0}").format(e))

    def before_insert(self):
        self.generate_key()

    def after_insert(self):
        if self.ticket_split_from:
            log_ticket_activity(
                self.name,
                "split the ticket from #{0}".format(self.ticket_split_from),
            )
            capture_event("ticket_split")
            return

        capture_event("ticket_created")
        publish_event("helpdesk:new-ticket", {"name": self.name})
        if self.get("description"):
            self.create_communication_via_contact(self.description, new_ticket=True)
            self.handle_inline_media_new_ticket()

        send_ack_email = frappe.db.get_single_value(
            "HD Settings", "send_acknowledgement_email"
        )
        if (
            not self.via_customer_portal
            and not frappe.flags.initial_sync
            and send_ack_email
        ):
            self.send_acknowledgement_email()

    def on_update(self):
        # flake8: noqa
        if self.status_category == "Open":
            if (
                self.get_doc_before_save()
                and self.get_doc_before_save().status_category != "Open"
            ):

                agents = self.get_assigned_agents()
                if agents:
                    for agent in agents:
                        self.notify_agent(agent.name, "Reaction")

        self.remove_assignment_if_not_in_team()
        self.publish_update()
        self.update_search_index()

    def notify_agent(self, agent, notification_type="Assignment"):
        frappe.get_doc(
            frappe._dict(
                doctype="HD Notification",
                user_from=frappe.session.user,
                reference_ticket=self.name,
                user_to=agent,
                notification_type=notification_type,
            )
        ).insert(ignore_permissions=True)

    def update_search_index(self):
        search = HelpdeskSearch()
        search.index_doc(self)

    def set_ticket_type(self):
        if self.ticket_type:
            return
        settings = frappe.get_doc("HD Settings")
        ticket_type = settings.default_ticket_type or DEFAULT_TICKET_TYPE
        self.ticket_type = ticket_type

    def set_raised_by(self):
        self.raised_by = self.raised_by or frappe.session.user

    def set_contact(self):
        email_id = parseaddr(self.raised_by)[1]
        # flake8: noqa
        if email_id:
            if not self.contact:
                contact = frappe.db.get_value("Contact", {"email_id": email_id})
                if contact:
                    self.contact = contact

    def set_customer(self):
        """
        Update `Customer` if does not exist already. `Contact` is assumed
        to be set beforehand.
        """
        # Skip if `Customer` is already set
        if self.customer:
            return

        if self.contact:
            customer = get_customer(self.contact)

            # let agent assign the customer when one contact has more than one customer
            if len(customer) == 1:
                self.customer = customer[0]

    def set_priority(self):
        if self.priority:
            return
        self.priority = (
            frappe.get_cached_value("HD Ticket Type", self.ticket_type, "priority")
            or frappe.get_cached_value("HD Settings", "HD Settings", "default_priority")
            or DEFAULT_TICKET_PRIORITY
        )

    def set_first_responded_on(self):
        if self.is_new():
            return
        if self.first_responded_on:
            return

        old_status_category = (
            self.get_doc_before_save().status_category
            if self.get_doc_before_save()
            else None
        )
        is_closed_or_resolved = (
            old_status_category == "Open" and self.status_category == "Resolved"
        )

        if self.status_category == "Paused" or is_closed_or_resolved:
            self.first_responded_on = frappe.utils.now_datetime()

    def set_feedback_values(self):
        if not self.feedback:
            return
        feedback_option = frappe.get_doc("HD Ticket Feedback Option", self.feedback)
        self.feedback_rating = feedback_option.rating

    def validate_ticket_type(self):
        settings = frappe.get_doc("HD Settings")
        if settings.is_ticket_type_mandatory and not self.ticket_type:
            frappe.throw(_("Ticket type is mandatory"))

    @property
    def has_agent_replied(self):
        return frappe.db.exists(
            "Communication",
            {
                "reference_doctype": "HD Ticket",
                "reference_name": self.name,
                "sent_or_received": "Sent",
            },
        )

    def validate_feedback(self):
        if (
            self.feedback
            or self.status_category != "Resolved"
            or is_agent()
            or not self.has_agent_replied
        ):
            return

        frappe.throw(
            _("Ticket must be resolved with a feedback"), frappe.ValidationError
        )

    def check_update_perms(self):
        if self.is_new() or is_agent():
            return
        old_doc = self.get_doc_before_save()
        is_closed = old_doc.status == "Closed"
        is_rated = bool(old_doc.feedback)
        if is_closed or is_rated:
            text = _("Closed or rated tickets cannot be updated by non-agents")
            frappe.throw(text, frappe.PermissionError)

    def handle_ticket_activity_update(self):
        """
        Handles the ticket activity update.
        Should be called inside on_update
        """
        field_maps = {
            "status": "status",
            "priority": "priority",
            "agent_group": "team",
            "ticket_type": "type",
            "contact": "contact",
        }
        for field in [
            "status",
            "priority",
            "agent_group",
            "contact",
            "ticket_type",
        ]:
            if self.has_value_changed(field):
                log_ticket_activity(
                    self.name, f"set {field_maps[field]} to {self.as_dict()[field]}"
                )

    def generate_key(self):
        self.key = uuid.uuid4()

    def remove_assignment_if_not_in_team(self):
        """
        Removes the assignment if the agent is not in the team.
        Should be called inside on_update
        """
        if self.is_new():
            return
        if not self.agent_group or (hasattr(self, "_assign") and not self._assign):
            return
        if self.has_value_changed("agent_group") and self.status_category == "Open":
            current_assigned_agent = self.get_assigned_agent()
            if not current_assigned_agent:
                return
            is_agent_in_assigned_team = self.agent_in_assigned_team(
                current_assigned_agent, self.agent_group
            )

            if (
                not is_agent_in_assigned_team
            ) and self.users_present_in_team_assignment_rule():
                clear_all_assignments("HD Ticket", self.name)
                frappe.publish_realtime(
                    "helpdesk:update-ticket-assignee",
                    {"ticket_id": self.name},
                    after_commit=True,
                )

    def agent_in_assigned_team(self, agent, team):
        return frappe.db.exists(
            "HD Team Member",
            {
                "parent": team,
                "user": agent,
            },
        )

    def users_present_in_team_assignment_rule(self):
        if not self.agent_group:
            return False

        assignment_rule = frappe.db.get_value(
            "HD Team", self.agent_group, "assignment_rule"
        )
        if not assignment_rule:
            return False

        is_disabled = frappe.db.get_value(
            "Assignment Rule", assignment_rule, "disabled"
        )
        if is_disabled:
            return False

        users = frappe.get_all(
            "Assignment Rule User", filters={"parent": assignment_rule}
        )
        if not users:
            return False

        return True

    @frappe.whitelist()
    def assign_agent(self, agent):
        assign({"assign_to": [agent], "doctype": "HD Ticket", "name": self.name})

        if frappe.session.user != agent:
            self.notify_agent(agent, "Assignment")

        publish_event("helpdesk:ticket-assignee-update", {"name": self.name})

    def get_assigned_agents(self):
        assignees = get_assignees({"doctype": "HD Ticket", "name": self.name})
        if len(assignees) > 0:
            names = [assignee.owner for assignee in assignees]
            return frappe.get_all("HD Agent", filters={"name": ["in", names]})

    def get_assigned_agent(self):
        # TODO: deprecate this
        # for some reason _assign is not set, maybe a framework bug?
        if hasattr(self, "_assign") and self._assign:
            assignees = json.loads(self._assign)
            if len(assignees) > 0:

                # TODO: temporary fix, remove this when only agents can be assigned to ticket
                exists = frappe.db.exists("HD Agent", assignees[0])
                if exists:
                    return assignees[0]

        assignees = get_assignees({"doctype": "HD Ticket", "name": self.name})
        if len(assignees) > 0:
            # TODO: temporary fix, remove this when only agents can be assigned to ticket
            return frappe.db.exists("HD Agent", assignees[0].owner)

        return None

    def on_trash(self):
        activities = frappe.db.get_all("HD Ticket Activity", {"ticket": self.name})
        for activity in activities:
            frappe.db.delete("HD Ticket Activity", activity)

        comments = frappe.db.get_all(
            "HD Ticket Comment", {"reference_ticket": self.name}
        )
        for comment in comments:
            frappe.db.delete("HD Ticket Comment", comment)

    def skip_email_workflow(self):
        skip: str = frappe.get_value("HD Settings", None, "skip_email_workflow") or "0"

        return bool(int(skip))

    def instantly_send_email(self):
        check: str = (
            frappe.get_value("HD Settings", None, "instantly_send_email") or "0"
        )

        return bool(int(check))

    @frappe.whitelist()
    def get_last_communication(self):
        filters = {
            "reference_doctype": "HD Ticket",
            "reference_name": ["=", str(self.name)],
        }

        try:
            communication = frappe.get_last_doc(
                "Communication",
                filters=filters,
            )

            return communication
        except Exception:
            return None

    def last_communication_email(self):
        if not (communication := self.get_last_communication()):
            return

        if not communication.email_account:
            return

        email_account = frappe.get_doc("Email Account", communication.email_account)

        if not email_account.enable_outgoing:
            return

        return email_account

    def sender_email(self):
        """
        Find an email to use as sender. Fall back through multiple choices

        :return: `Email Account`
        """
        if email_account := self.last_communication_email():
            return email_account

        if email_account := default_ticket_outgoing_email_account():
            return email_account

        if email_account := default_outgoing_email_account():
            return email_account

    @property
    def portal_uri(self):
        root_uri = frappe.utils.get_url()
        return f"{root_uri}/helpdesk/my-tickets/{self.name}"

    @frappe.whitelist()
    def new_comment(self, content: str, attachments: List[str] = []):
        if not is_agent():
            frappe.throw(
                _("You are not permitted to add a comment"), frappe.PermissionError
            )
        c = frappe.new_doc("HD Ticket Comment")
        c.commented_by = frappe.session.user
        c.content = content
        c.is_pinned = False
        c.reference_ticket = self.name
        c.save()
        for attachment in attachments:
            self.attach_file_with_doc(
                "HD Ticket Comment", c.name, attachment.get("file_url")
            )

    @frappe.whitelist()
    def reply_via_agent(
        self,
        message: str,
        to: str = None,
        cc: str = None,
        bcc: str = None,
        attachments: List[str] = [],
    ):
        skip_email_workflow = self.skip_email_workflow()
        medium = "" if skip_email_workflow else "Email"
        subject = f"Re: {self.subject}"
        sender = frappe.session.user
        recipients = to or self.raised_by
        sender_email = None if skip_email_workflow else self.sender_email()

        if recipients == "Administrator":
            admin_email = frappe.get_value("User", "Administrator", "email")
            recipients = admin_email

        communication = frappe.get_doc(
            {
                "bcc": bcc,
                "cc": cc,
                "communication_medium": medium,
                "communication_type": "Communication",
                "content": message,
                "doctype": "Communication",
                "email_account": sender_email.name if sender_email else None,
                "email_status": "Open",
                "recipients": recipients,
                "reference_doctype": "HD Ticket",
                "reference_name": self.name,
                "sender": sender,
                "sent_or_received": "Sent",
                "status": "Linked",
                "subject": subject,
            }
        )

        last_communication = self.get_last_communication()
        if last_communication and last_communication.message_id:
            communication.in_reply_to = last_communication.name

        communication.insert(ignore_permissions=True)
        capture_event("agent_replied")

        if skip_email_workflow or not frappe.db.get_single_value(
            "HD Settings", "enable_reply_email_via_agent"
        ):
            return

        if not sender_email:
            frappe.throw(_("Can not send email. No sender email set up!"))

        _attachments = []

        for attachment in attachments:
            file_doc = frappe.get_doc("File", attachment)
            file_doc.attached_to_name = communication.name
            file_doc.attached_to_doctype = "Communication"
            file_doc.save(ignore_permissions=True)
            self.attach_file_with_doc("HD Ticket", self.name, file_doc.file_url)

            _attachments.append({"file_url": file_doc.file_url})

        message = self.parse_content(message)

        reply_to_email = sender_email.email_id
        rendered_template: str | None = None
        if self.via_customer_portal:
            email_content = frappe.db.get_single_value(
                "HD Settings", "reply_via_agent_email_content"
            )
            default_email_content = get_default_email_content("reply_via_agent")
            try:
                rendered_template = self._get_rendered_template(
                    email_content,
                    default_email_content,
                    {"message": message, "ticket_url": self.portal_uri},
                )
            except Exception as e:
                frappe.throw(_("Could not an email due to: {0}").format(e))

        send_delayed = True
        send_now = False

        if self.instantly_send_email():
            send_delayed = False
            send_now = True

        try:
            frappe.sendmail(
                attachments=_attachments,
                bcc=bcc,
                cc=cc,
                communication=communication.name,
                delayed=send_delayed,
                expose_recipients="header",
                message=rendered_template if rendered_template is not None else message,
                as_markdown=True,
                now=send_now,
                recipients=recipients,
                reference_doctype="HD Ticket",
                reference_name=self.name,
                reply_to=reply_to_email,
                sender=reply_to_email,
                subject=subject,
                with_container=False,
                in_reply_to=last_communication.name
                if last_communication.name
                else None,
            )
        except Exception as e:
            frappe.throw(_(e))

    @frappe.whitelist()
    # flake8: noqa
    def create_communication_via_contact(
        self, message, attachments=[], new_ticket=False
    ):

        if not new_ticket and frappe.db.get_single_value(
            "HD Settings", "enable_reply_email_to_agent"
        ):
            # send email to assigned agents
            self.send_reply_email_to_agent()

        # if self.status_category == "Paused" and not new_ticket:
        if not new_ticket:
            self.status = self.ticket_reopen_status
            self.save(ignore_permissions=True)

        c = frappe.new_doc("Communication")
        c.communication_type = "Communication"
        c.communication_medium = "Email"
        c.sent_or_received = "Received"
        c.email_status = "Open"
        c.subject = f"Re: {self.subject}"
        c.sender = frappe.session.user
        c.content = message
        c.status = "Linked"
        c.reference_doctype = "HD Ticket"
        c.reference_name = self.name
        c.ignore_permissions = True
        c.ignore_mandatory = True
        c.save(ignore_permissions=True)

        _attachments = self.get("attachments") or attachments or []
        if not len(_attachments):
            return
        QBFile = frappe.qb.DocType("File")
        condition_name = [QBFile.name == i["name"] for i in _attachments]
        frappe.qb.update(QBFile).set(QBFile.attached_to_name, c.name).set(
            QBFile.attached_to_doctype, "Communication"
        ).where(Criterion.any(condition_name)).run()

        # attach files to ticket
        file_urls = frappe.get_all(
            "File", filters={"attached_to_name": c.name}, pluck="file_url"
        )
        for url in file_urls:
            self.attach_file_with_doc("HD Ticket", self.name, url)

    def handle_inline_media_new_ticket(self):
        soup = BeautifulSoup(self.description, "html.parser")
        files = []  # List of file URLs
        for tag in soup.find_all(["img", "video"]):
            if tag.has_attr("src"):
                src = tag["src"]
                files.append(src)
        for f in files:
            file = frappe.db.exists(
                "File",
                {
                    "file_url": f,
                    "attached_to_doctype": ["is", "Not Set"],
                    "owner": frappe.session.user,
                },
            )
            if file:
                doc = frappe.get_doc("File", file)
                doc.attached_to_doctype = "HD Ticket"
                doc.attached_to_name = self.name
                doc.save()

    def send_reply_email_to_agent(self):
        assigned_agents = self.get_assigned_agents()
        if not assigned_agents:
            return

        recipients = [a.get("name") for a in self.get_assigned_agents()]

        email_content = frappe.db.get_single_value(
            "HD Settings", "reply_email_to_agent_content"
        )
        default_email_content = get_default_email_content("reply_to_agents")
        try:
            frappe.sendmail(
                recipients=recipients,
                subject=f"Re: {self.subject} - #{self.name}",
                message=self._get_rendered_template(
                    email_content,
                    default_email_content,
                    {
                        "ticket_url": frappe.utils.get_url(
                            "/helpdesk/tickets/" + str(self.name)
                        )
                    },
                ),
                reference_doctype="HD Ticket",
                reference_name=self.name,
                now=True,
            )
        except Exception as e:
            frappe.throw(_(e))

    def send_acknowledgement_email(self):

        acknowledgement_email_content = frappe.db.get_single_value(
            "HD Settings", "acknowledgement_email_content"
        )
        default_acknowledgement_email_content = get_default_email_content(
            "acknowledgement"
        )

        try:
            frappe.sendmail(
                recipients=[self.raised_by],
                subject=f"Ticket #{self.name}: We've received your request",
                message=self._get_rendered_template(
                    acknowledgement_email_content,
                    default_acknowledgement_email_content,
                ),
                reference_doctype="HD Ticket",
                reference_name=self.name,
                now=True,
                expose_recipients="header",
                email_headers={"X-Auto-Generated": "hd-acknowledgement"},
            )
        except Exception as e:
            frappe.throw(
                _("Could not send an acknowledgement email due to: {0}").format(e)
            )

    @frappe.whitelist()
    def mark_seen(self):
        self.add_viewed(
            unique_views=True, force=True
        )  # Document class method, no way to add unique_views via document settings, hence used force and unique_views=True
        clear_notifications(ticket=self.name)

    def get_escalation_rule(self):
        filters = [
            {
                "priority": self.priority,
                "team": self.agent_group,
                "ticket_type": self.ticket_type,
            },
            {
                "priority": self.priority,
                "team": self.agent_group,
            },
            {
                "priority": self.priority,
                "ticket_type": self.ticket_type,
            },
            {
                "team": self.agent_group,
                "ticket_type": self.ticket_type,
            },
            {
                "priority": self.priority,
            },
            {
                "team": self.agent_group,
            },
            {
                "ticket_type": self.ticket_type,
            },
        ]

        for i in range(len(filters)):
            try:
                f = {
                    **filters[i],
                    "is_enabled": True,
                }
                rule = frappe.get_last_doc("HD Escalation Rule", filters=f)
                if rule:
                    return rule
            except Exception:
                pass

    def apply_escalation_rule(self):
        if not self.status_category == "Open" or self.is_new():
            return
        escalation_rule = self.get_escalation_rule()
        if not escalation_rule:
            return
        self.agent_group = escalation_rule.to_team or self.agent_group
        self.priority = escalation_rule.to_priority or self.priority
        self.ticket_type = escalation_rule.to_ticket_type or self.ticket_type

        if escalation_rule.to_agent:
            self.assign_agent(escalation_rule.to_agent)

    def set_sla(self):
        """
        Find an SLA to apply to this ticket.
        """
        if sla := get_sla(self):
            self.sla = sla.name

    def apply_sla(self):
        """
        Apply SLA if set.
        """
        if sla := frappe.get_last_doc("HD Service Level Agreement", {"name": self.sla}):
            sla.apply(self)

    def set_default_status(self):
        if self.is_new():
            self.status = self.default_open_status

    def set_status_category(self):
        self.status_category = self.status_category or frappe.get_value(
            "HD Ticket Status",
            self.status,
            "category",
        )

    # `on_communication_update` is a special method exposed from `Communication` doctype.
    # It is called when a communication is updated. Beware of changes as this effectively
    # is an external dependency. Refer `communication.py` of Frappe framework for more.
    # Since this is called from communication itself, `c` is the communication doc.
    def on_communication_update(self, c):
        # If communication is incoming, then it is a reply from customer, and ticket must
        # be reopened.
        # handle re opening tickets for email
        if c.sent_or_received == "Received":
            # check if agent has replied

            if self.has_agent_replied:
                self.status = self.ticket_reopen_status
            else:
                self.status = self.default_open_status
        # If communication is outgoing, it must be a reply from agent
        if c.sent_or_received == "Sent":
            # Set first response date if not set already
            self.first_responded_on = (
                self.first_responded_on or frappe.utils.now_datetime()
            )

            # TODO: remove this feature once we add automation feature
            if frappe.db.get_single_value("HD Settings", "auto_update_status"):
                self.status = frappe.db.get_single_value(
                    "HD Settings", "update_status_to"
                )

        # Fetch description from communication if not set already. This might not be needed
        # anymore as a communication is created when a ticket is created.
        self.description = self.description or c.content
        # Save the ticket, allowing for hooks to run.
        self.save()

    def attach_file_with_doc(self, doctype, docname, file_url):
        file_doc = frappe.new_doc("File")
        file_doc.attached_to_doctype = doctype
        file_doc.attached_to_name = docname
        file_doc.file_url = file_url
        file_doc.save(ignore_permissions=True)

    @staticmethod
    def default_list_data(show_customer_portal_fields=False):
        columns = [
            {
                "label": "ID",
                "type": "Int",
                "key": "name",
                "width": "5rem",
            },
            {
                "label": "Subject",
                "type": "Data",
                "key": "subject",
                "width": "25rem",
            },
            {
                "label": "Status",
                "type": "Select",
                "key": "status",
                "width": "8rem",
            },
            {
                "label": "First response",
                "type": "Datetime",
                "key": "response_by",
                "width": "8rem",
            },
            {
                "label": "Resolution",
                "type": "Datetime",
                "key": "resolution_by",
                "width": "8rem",
            },
            {
                "label": "Assigned To",
                "type": "MultipleAvatar",
                "key": "_assign",
                "width": "8rem",
            },
            {
                "label": "Customer",
                "type": "Link",
                "key": "customer",
                "options": "HD Customer",
                "width": "8rem",
            },
            {
                "label": "Priority",
                "type": "Link",
                "options": "HD Ticket Priority",
                "key": "priority",
                "width": "10rem",
            },
            {
                "label": "Type",
                "type": "Link",
                "options": "HD Ticket Type",
                "key": "ticket_type",
                "width": "11rem",
            },
            {
                "label": "Team",
                "type": "Link",
                "options": "HD Team",
                "key": "agent_group",
                "width": "10rem",
            },
            {
                "label": "Contact",
                "type": "Link",
                "key": "contact",
                "options": "Contact",
                "width": "8rem",
            },
            {
                "label": "Rating",
                "type": "Rating",
                "key": "feedback_rating",
                "width": "10rem",
            },
            {
                "label": "Created",
                "type": "Datetime",
                "key": "creation",
                "options": "Contact",
                "width": "8rem",
            },
        ]
        customer_portal_columns = [
            {
                "label": "ID",
                "type": "Int",
                "key": "name",
                "width": "5rem",
            },
            {
                "label": "Subject",
                "type": "Data",
                "key": "subject",
                "width": "22rem",
            },
            {
                "label": "Status",
                "type": "Select",
                "key": "status",
                "width": "11rem",
            },
            {
                "label": "Priority",
                "type": "Link",
                "options": "HD Ticket Priority",
                "key": "priority",
                "width": "10rem",
            },
            {
                "label": "First response",
                "type": "Datetime",
                "key": "response_by",
                "width": "8rem",
            },
            {
                "label": "Resolution",
                "type": "Datetime",
                "key": "resolution_by",
                "width": "8rem",
            },
            {
                "label": "Team",
                "type": "Link",
                "options": "HD Team",
                "key": "agent_group",
                "width": "10rem",
            },
            {
                "label": "Created",
                "type": "Datetime",
                "key": "creation",
                "options": "Contact",
                "width": "8rem",
            },
        ]
        rows = [
            "name",
            "subject",
            "status",
            "priority",
            "ticket_type",
            "agent_group",
            "contact",
            "agreement_status",
            "response_by",
            "resolution_by",
            "customer",
            "first_responded_on",
            "modified",
            "creation",
            "_assign",
            "resolution_date",
        ]
        return {
            "columns": customer_portal_columns
            if show_customer_portal_fields
            else columns,
            "rows": rows,
        }

    def parse_content(self, content):
        """
        Finds 'src' attribute of img/video and replaces it  with 'embed' attribute
        embed tag is important because framework replaces it with <img src="cid:content_id">
        this in turn is displayed as an image in the mail sent to the customer
        """
        if not content:
            return ""

        soup = BeautifulSoup(content, "html.parser")

        for tag in soup.find_all(["img", "video"]):
            if tag.name == "img":
                tag["embed"] = tag.get("src")
                tag["width"] = "80%"
                tag["height"] = "80%"
                del tag["src"]
            elif tag.name == "video":
                tag["embed"] = tag.get("src")
                del tag["src"]

        return str(soup)

    @staticmethod
    def filter_standard_fields(fields):
        for f in fields:
            if f["name"] in customer_not_allowed_fields:
                fields.remove(f)
        return fields


# Check if `user` has access to this specific ticket (`doc`). This implements extra
# permission checks which is not possible with standard permission system. This function
# is being called from hooks. `doc` is the ticket to check against
def has_permission(doc, user=None):

    if not user:
        user = frappe.session.user

    if (
        doc.contact == user
        or doc.raised_by == user
        or doc.owner == user
        or is_admin(user)
        or doc.customer in get_customer(user)
    ):
        return True

    if not is_agent(user):
        return False

    enable_restrictions = frappe.db.get_single_value(
        "HD Settings", "restrict_tickets_by_agent_group"
    )
    if not enable_restrictions:
        return True
    show_tickets_without_team = frappe.db.get_single_value(
        "HD Settings", "do_not_restrict_tickets_without_an_agent_group"
    )
    if show_tickets_without_team and not doc.get("agent_group"):
        return True

    teams = get_agents_team()
    if any([team.get("ignore_restrictions") for team in teams]):
        return True

    team_names = [t.team_name for t in teams]
    exists = frappe.db.exists(
        "HD Team Member", {"parent": ["in", team_names], "user": frappe.session.user}
    )
    if exists and doc.get("agent_group") in team_names:
        return True

    return False


# Custom perms for list query. Only the `WHERE` part
# https://frappeframework.com/docs/user/en/python-api/hooks#modify-list-query
def permission_query(user):

    if not user:
        user = frappe.session.user
    if is_admin(user):
        return

    #  To handle the case for normal users i.e. not agents
    customer = get_customer(user)
    query = "(`tabHD Ticket`.owner = {user} OR `tabHD Ticket`.contact = {user} OR `tabHD Ticket`.raised_by = {user})".format(
        user=frappe.db.escape(user)
    )
    for c in customer:
        query += " OR `tabHD Ticket`.customer={customer}".format(
            customer=frappe.db.escape(c)
        )

    if not is_agent(user):
        return query

    enable_restrictions = frappe.db.get_single_value(
        "HD Settings", "restrict_tickets_by_agent_group"
    )
    if not enable_restrictions:
        return  # If not enabled, return all tickets

    show_tickets_without_team = frappe.db.get_single_value(
        "HD Settings", "do_not_restrict_tickets_without_an_agent_group"
    )

    teams = get_agents_team()

    if show_tickets_without_team:
        query += " OR (`tabHD Ticket`.agent_group is null OR `tabHD Ticket`.agent_group = '')"

    # If agent belongs to the team which has ignore_permission set to 1.
    # that means this team can see all the tickets without any restriction,
    # Event the other team's tickets.
    if any(team.get("ignore_restrictions") for team in teams):
        all_teams = frappe.get_all("HD Team", pluck="name")
        if not all_teams:
            return query
        all_teams = ", ".join(f"'{team}'" for team in all_teams)
        query += f" OR (`tabHD Ticket`.agent_group in ({all_teams}))".format(
            all_teams=all_teams
        )
        if not show_tickets_without_team:
            query += " OR (`tabHD Ticket`.agent_group is null)"
        return query

    team_names = [t.get("team_name") for t in teams]

    if not team_names:
        return query

    # Here we will apply the restriction based on the teams the agent belongs to.
    team_names = ", ".join(f"'{team}'" for team in team_names)
    query += f" OR (`tabHD Ticket`.agent_group in ({team_names}))".format(
        team_names=team_names
    )
    return query


def set_guest_ticket_creation_permission():
    doctype = "HD Ticket"
    add_permission(doctype, "Guest", 0)

    role = "Guest"
    permlevel = 0
    ptype = ["read", "write", "create", "if_owner"]

    for p in ptype:
        # update permissions
        update_permission_property(doctype, role, permlevel, p, 1)


def remove_guest_ticket_creation_permission():
    doctype = "HD Ticket"
    role = "Guest"
    permlevel = 0
    remove(doctype, role, permlevel, 1)


customer_not_allowed_fields = ["customer"]


def close_tickets_after_n_days():
    if frappe.db.get_single_value("HD Settings", "auto_close_tickets") == 0:
        return

    status, days_threshold = frappe.db.get_value(
        "HD Settings", "HD Settings", ["auto_close_status", "auto_close_after_days"]
    )

    tickets_to_close = (
        frappe.db.sql(
            """
                SELECT t.name
                FROM `tabHD Ticket` t
                INNER JOIN (
                    SELECT reference_name, MAX(communication_date) as last_communication_date
                    FROM `tabCommunication` 
                    WHERE reference_doctype = 'HD Ticket'
                    GROUP BY reference_name
                ) latest_comm ON t.name = latest_comm.reference_name
                WHERE t.status = %(status)s
                AND latest_comm.last_communication_date < DATE_SUB(NOW(), INTERVAL %(days_threshold)s DAY)
            """,
            {"days_threshold": days_threshold, "status": status},
            pluck="name",
        )
        or []
    )
    tickets_to_close = list(set(tickets_to_close))

    # cant do set_value because SLA will not be applied as setting directly to db and doc is not running.
    for ticket in tickets_to_close:
        doc = frappe.get_doc("HD Ticket", ticket)
        doc.status = "Closed"
        doc.flags.ignore_validate = True
        doc.save(ignore_permissions=True)
        frappe.db.commit()  # nosemgrep
