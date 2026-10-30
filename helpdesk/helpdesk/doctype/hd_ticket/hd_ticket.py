import json
import uuid
from contextlib import contextmanager
from datetime import timedelta
from email.utils import parseaddr
from functools import lru_cache

import frappe
from bs4 import BeautifulSoup
from frappe import _
from frappe.core.page.permission_manager.permission_manager import remove
from frappe.desk.form.assign_to import add as assign
from frappe.desk.form.assign_to import clear as clear_all_assignments
from frappe.desk.form.assign_to import get as get_assignees
from frappe.model.document import Document
from frappe.permissions import add_permission, update_permission_property
from frappe.query_builder import DocType, Order
from frappe.utils import add_to_date, getdate, now_datetime
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
    get_doc_room,
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
        room = get_doc_room("HD Ticket", self.name)
        publish_event(
            "helpdesk:ticket-update", room=room, data={"ticket_id": self.name}
        )

    def autoname(self):
        return self.name

    def before_insert(self):
        self.generate_key()
        self._apply_facility_routing()
        self._set_priority_from_keywords()

    def after_insert(self):
        self._remember_contact_location()

    def _apply_facility_routing(self):
        """Auto-populate facility, county, sub_county and assign to L0 team.

        Story County-2: AC — auto-routing engine.
        Story 354: Extended to honour user-supplied county/sub_county and to
        route by county+sub_county when the user has no facility set.

        Priority order:
        1. Facility from User.facility → look up HD Facility Mapping by facility.
        2. User-supplied county + sub_county → look up HD Facility Mapping by
           county + sub_county (e.g. from the ticket creation picker).
        3. Fall back to the default national team.
        """
        raised_by = self.raised_by or frappe.session.user
        if not raised_by or raised_by == "Guest":
            return

        # Skip entirely for tickets raised by an L2 agent -- l2_raised_routing.py
        # (before_insert) has already forced this ticket to National Support, and
        # facility/county geography should not override that business rule.
        if frappe.db.exists("HD Agent", raised_by) and self.get("brand") not in self.PRODUCT_BRANDS:
            agent_teams = frappe.get_all("HD Team Member", filters={"user": raised_by}, pluck="parent")
            if any(t not in ("National Support", "Engineering Team") for t in agent_teams):
                return

        # Step 1: get facility from user profile; form-supplied facility takes priority
        user_facility = frappe.db.get_value("User", raised_by, "facility")
        effective_facility = self.facility or user_facility

        # Always stamp the facility on the ticket if we know it
        if effective_facility and not self.facility:
            self.facility = effective_facility

        # Auto-fill county + sub_county from the selected facility record
        if effective_facility and (not self.county or not self.sub_county):
            fac = frappe.db.get_value(
                "HD Facility",
                effective_facility,
                ["county", "subcounty"],
                as_dict=True,
            )
            if fac:
                if  fac.county and not self.county:
                    self.county = fac.county
                if fac.subcounty and not self.sub_county:
                    self.sub_county = fac.subcounty

        # Careverse tickets keep Careverse Team regardless of facility geography.
        # (County/sub-county were already filled in above, for reporting.)
        if self._is_careverse_ticket():
            team = frappe.db.get_value("HD Brand", "Careverse", "default_team")
            if team:
                self.agent_group = team
                self.support_level = frappe.db.get_value("HD Team", team, "support_level")
            return

        mapping = None

        if effective_facility:
            # Step 2a: look up HD Facility Mapping by facility name
            mapping = frappe.db.get_value(
                "HD Facility Mapping",
                self._mapping_filters({"facility_name": effective_facility}),
                ["sub_county", "county", "l0_team", "l1_team", "l2_team"],
                as_dict=True,
            )

        if not mapping and self.county and self.sub_county:
            # Step 2b: no facility mapping — try to match by county + sub_county
            # (user explicitly chose them via the ticket creation form or facility picker)
            mapping = frappe.db.get_value(
                "HD Facility Mapping",
                self._mapping_filters({"county": self.county, "sub_county": self.sub_county}),
                ["sub_county", "county", "l0_team", "l1_team", "l2_team"],
                as_dict=True,
            )

        if not mapping and self.get("brand") in self.PRODUCT_BRANDS:
            team = frappe.db.get_value("HD Brand", self.brand, "default_team")
            if team:
                self.agent_group = team
                self.support_level = frappe.db.get_value("HD Team", team, "support_level")
            return

        if mapping:
            # Step 3: populate geography — don't overwrite user-supplied values
            if not self.sub_county:
                self.sub_county = mapping.sub_county
            if not self.county:
                self.county = mapping.county

            # Step 4: assign to l0_team, fall back to l1_team if l0 not set.
            # Always override agent_group when a mapping gives us a specific team
            # so that template defaults (e.g. "Nairobi") don't win over geography.
            assigned_team = mapping.l0_team or mapping.l1_team
            if assigned_team:
                self.agent_group = assigned_team
                self.support_level = frappe.db.get_value(
                    "HD Team", assigned_team, "support_level"
                )
        else:
            # Step 6: no mapping — try to route by county to l1_team.
            # Always override agent_group from county lookup so template
            # defaults don't persist when we know the correct regional team.
            if self.county:
                county_team = _get_team_for_county(self.county)
                if county_team:
                    self.agent_group = county_team
                    self.support_level = frappe.db.get_value(
                        "HD Team", county_team, "support_level"
                    )

            # Step 7: final fallback — national team only if still unassigned
            if not self.agent_group:
                national_team = _get_default_national_team()
                if national_team:
                    self.agent_group = national_team

    PRODUCT_BRANDS = ("Admin Central", "F360", "P360")

    def _mapping_filters(self, base):
        """Facility Mapping lookups are per product: product brands only see their own
        mappings; everything else only sees mappings with no product."""
        flt = [[k, "=", v] for k, v in base.items()]
        if self.get("brand") in self.PRODUCT_BRANDS:
            flt.append(["product", "=", self.brand])
        else:
            flt.append(["product", "is", "not set"])
        return flt

    def _is_careverse_ticket(self):
        """True if this ticket belongs to the Careverse workflow: brand set, or
        received on the Careverse brand's support mailbox. Works whether or not
        the brand hook has already run."""
        if self.get("brand") == "Careverse":
            return True
        if self.get("email_account"):
            addr = frappe.db.get_value("Email Account", self.email_account, "email_id")
            if addr:
                return frappe.db.get_value(
                    "HD Brand", {"support_email": addr, "is_active": 1}, "name"
                ) == "Careverse"
        return False

    def _remember_contact_location(self):
        """Persist county + sub_county to HD Customer after ticket insert.

        Story 354: Auto-remember — when a ticket is created with county/sub_county,
        update the HD Customer record so the next ticket creation can pre-fill them.
        Only updates if values are non-empty.
        """
        if not self.county and not self.sub_county:
            return

        if not self.contact:
            return

        from helpdesk.utils import get_customer

        customers = get_customer(self.contact)
        if not customers:
            return

        customer_name = customers[0]
        update_vals = {}
        if self.county:
            update_vals["county"] = self.county
        if self.sub_county:
            update_vals["sub_county"] = self.sub_county

        if update_vals:
            frappe.db.set_value("HD Customer", customer_name, update_vals)

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
        self.validate_priority_matrix()
        self.validate_category()
        self.validate_checklist_before_resolution()

    def validate_checklist_before_resolution(self):
        """Prevent resolution/closure when mandatory checklist items are incomplete.

        Story 1.9: AC #8 — server-side authoritative guard.
        Checks both "Resolved" and "Closed" status categories so that tickets
        cannot be closed (manually or via auto-close scheduler) with incomplete
        mandatory checklist items.

        Only fires on status transitions (not general saves of already-resolved
        tickets) to allow actions like re-applying an incident model without
        blocking the save with newly-added incomplete items.
        """
        if getattr(self.flags, "allow_plugin_status_change", False):
            return
        if self.status_category not in ("Resolved", "Closed"):
            return

        # Only enforce on status transitions, not on saves where status is
        # already resolved/closed (e.g. re-applying an incident model)
        if not self.has_value_changed("status"):
            return

        checklist = self.get("ticket_checklist", [])
        if not checklist:
            return

        incomplete_mandatory = [
            row.item
            for row in checklist
            if row.is_mandatory and not row.is_completed
        ]

        if incomplete_mandatory:
            item_list = ", ".join(f'"{i}"' for i in incomplete_mandatory)
            frappe.throw(
                _(
                    "Cannot resolve ticket: {0} mandatory checklist item(s) must be "
                    "completed first: {1}"
                ).format(len(incomplete_mandatory), item_list),
                frappe.ValidationError,
            )

    def validate_priority_matrix(self):
        """Calculate priority from Impact x Urgency matrix when ITIL Mode is enabled.

        AC #7: Server-side authority — client JS is UX only, server always wins.
        AC #10: Short-circuits immediately when ITIL mode is off.
        AC #6: Skips calculation when impact or urgency is empty (legacy tickets).
        """
        if not frappe.db.get_single_value("HD Settings", "itil_mode_enabled"):
            return

        if not self.impact or not self.urgency:
            # Legacy ticket: both fields empty — retain manually-set priority (AC #6)
            return

        matrix_json = frappe.db.get_single_value("HD Settings", "priority_matrix")
        if not matrix_json:
            return

        if isinstance(matrix_json, str):
            matrix = json.loads(matrix_json)
        else:
            matrix = matrix_json

        key = f"{self.impact}-{self.urgency}"
        calculated_priority = matrix.get(key)
        if calculated_priority:
            self.priority = calculated_priority

    def validate_category(self):
        """Enforce category requirement on resolution and sub_category parent match.

        AC #7: category required when resolving if setting is enabled.
        AC #8: sub_category must belong to selected category.
        """
        if getattr(self.flags, "allow_plugin_status_change", False):
            return
        is_resolving = self.status_category == "Resolved"

        if is_resolving and frappe.db.get_single_value(
            "HD Settings", "category_required_on_resolution"
        ):
            if not self.category:
                frappe.throw(
                    _("A category must be selected before resolving this ticket."),
                    frappe.ValidationError,
                )

        if self.sub_category and self.category:
            parent = frappe.db.get_value(
                "HD Ticket Category", self.sub_category, "parent_category"
            )
            if parent != self.category:
                frappe.throw(
                    _(
                        "Sub Category '{0}' does not belong to Category '{1}'."
                    ).format(self.sub_category, self.category),
                    frappe.ValidationError,
                )

    def before_save(self):
        self.apply_sla()
        if not self.is_new():
            self.handle_ticket_activity_update()
            self._check_priority_escalation()

        self.handle_email_feedback()

        if self.is_new():
            self.raised_outside_working_hours = (
                self.is_currently_outside_working_hours()
            )

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

    def after_insert(self):

        # Telemetry Event
        self.capture_ticket_created_telemetry_events()
        publish_event("helpdesk:new-ticket")

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

    def capture_ticket_created_telemetry_events(self):
        if self.subject == "Welcome to ServiceDesk":
            return

        capture_event("ticket_created")
        if not self.via_customer_portal:
            capture_event("ticket_created_via_email")
        if self.via_customer_portal and not is_agent():
            capture_event("ticket_created_via_customer")

        if self.ticket_split_from:
            log_ticket_activity(
                self.name,
                "split the ticket from #{0}".format(self.ticket_split_from),
            )
            capture_event("ticket_split")

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
                        if agent.name == frappe.session.user:
                            continue
                        self.notify_agent(agent.name, "Reaction")

        # SLA reset: when resolution_by changes (SLA recalculated, ticket reopened,
        # SLA policy changed), clear dedup keys so warnings fire again for the new cycle.
        if not self.is_new() and self.has_value_changed("resolution_by"):
            try:
                from helpdesk.helpdesk.doctype.hd_service_level_agreement.sla_monitor import (
                    clear_warning_dedup,
                )
                clear_warning_dedup(str(self.name))
            except Exception:
                frappe.log_error(
                    title=f"SLA Monitor: clear_warning_dedup failed for {self.name}",
                    message=frappe.get_traceback(),
                )

        self.remove_assignment_if_not_in_team()
        self.publish_update()
        self.capture_update_telemetry_events()

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

    def capture_update_telemetry_events(self):
        capture_event("ticket_updated")

        if self.has_value_changed("status"):
            capture_event("ticket_status_updated")
            self.notify_customer_of_status_change()
            self._run_escalation_rules("status_change")
            if self.status_category == "Resolved":
                self._send_resolution_confirmation_email()

        if self.has_value_changed("priority"):
            self._run_escalation_rules("priority_match")

        if (
            self.has_value_changed("agreement_status")
            and self.agreement_status == "Failed"
        ):
            self._run_escalation_rules("sla_breach")

        if (
            self.has_value_changed("status_category")
            and self.status_category == "Resolved"
        ):
            capture_event("ticket_resolved")

    def _run_escalation_rules(self, trigger: str) -> None:
        try:
            from helpdesk.helpdesk.doctype.hd_ticket.escalation_rule_engine import evaluate_rules
            evaluate_rules(self, trigger)
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"Escalation rules failed [{trigger}]")

    def notify_customer_of_status_change(self):
        """Send email to the customer when an agent changes the ticket status."""
        try:
            skip_email_workflow = self.skip_email_workflow()
            if skip_email_workflow:
                return

            customer_email = self.raised_by
            if not customer_email or customer_email in ("Administrator", "Guest", ""):
                return

            changer = frappe.session.user
            if changer == customer_email:
                return

            old_status = (
                self.get_doc_before_save().status
                if self.get_doc_before_save()
                else None
            )
            new_status = self.status
            if old_status == new_status:
                return

            portal_link = frappe.utils.get_url(f"/helpdesk/my-tickets/{self.name}")

            frappe.sendmail(
                recipients=[customer_email],
                subject=f"Ticket #{self.name} status updated to {new_status}",
                template="ticket_status_change_notification",
                args={
                    "ticket_id": self.name,
                    "ticket_subject": self.subject,
                    "old_status": old_status or "N/A",
                    "new_status": new_status,
                    "portal_link": portal_link,
                },
                reference_doctype="HD Ticket",
                reference_name=self.name,
            )
        except Exception:
            frappe.log_error(frappe.get_traceback(), "Status Change Notification Error")

        self._create_customer_status_notification(old_status=None, new_status=self.status)

    def _send_resolution_confirmation_email(self):
        """
        Notify the customer that their ticket was resolved.
        If they are online (portal), fire a realtime event so a dialog appears immediately.
        Always also send an email as a fallback for users who are offline.
        """
        try:
            customer_email = self.raised_by
            if not customer_email or customer_email in ("Administrator", "Guest", ""):
                return

            if not self.key:
                return

            # Realtime popup for users currently on the portal
            frappe.publish_realtime(
                "helpdesk:resolution-confirm",
                {
                    "ticket_id": self.name,
                    "ticket_subject": self.subject,
                    "key": str(self.key),
                },
                user=customer_email,
                after_commit=True,
            )

            # Email fallback for offline users
            base_url = frappe.utils.get_url()
            yes_link = f"{base_url}/api/method/helpdesk.api.resolution_confirm.confirm?key={self.key}&answer=yes"
            no_link = f"{base_url}/api/method/helpdesk.api.resolution_confirm.confirm?key={self.key}&answer=no"

            frappe.sendmail(
                recipients=[customer_email],
                subject=f"Has your issue been resolved? — Ticket #{self.name}",
                template="resolution_confirmation",
                args={
                    "ticket_id": self.name,
                    "ticket_subject": self.subject,
                    "yes_link": yes_link,
                    "no_link": no_link,
                },
                reference_doctype="HD Ticket",
                reference_name=self.name,
            )
        except Exception:
            frappe.log_error(frappe.get_traceback(), "Resolution Confirmation Email Error")

    def _create_customer_reply_notification(self, message: str, communication_name: str):
        """Create an in-app notification for the customer when an agent replies."""
        try:
            customer_email = self.raised_by
            if not customer_email or customer_email in ("Administrator", "Guest", ""):
                return
            agent = frappe.session.user
            if agent == customer_email:
                return
            from bs4 import BeautifulSoup
            plain_preview = BeautifulSoup(message or "", "html.parser").get_text(" ", strip=True)[:300]
            agent_name = frappe.db.get_value("User", agent, "full_name") or agent
            frappe.get_doc({
                "doctype": "HD Notification",
                "user_from": agent,
                "user_to": customer_email,
                "notification_type": "Ticket Reply",
                "reference_ticket": self.name,
                "message": plain_preview,
                "read": 0,
            }).insert(ignore_permissions=True)
        except Exception:
            frappe.log_error(frappe.get_traceback(), "Customer reply notification error")

    def _notify_agents_of_customer_reply(self, message: str):
        """Create in-app bell notifications for assigned agents when customer replies."""
        try:
            assigned_agents = self.get_assigned_agents() or []
            customer = frappe.session.user
            customer_name = frappe.db.get_value("User", customer, "full_name") or customer
            from bs4 import BeautifulSoup
            plain_preview = BeautifulSoup(message or "", "html.parser").get_text(" ", strip=True)[:300]
            from helpdesk.helpdesk.doctype.hd_notification.utils import create_notification
            for agent in assigned_agents:
                agent_email = agent.get("name")
                if not agent_email or agent_email == customer:
                    continue
                create_notification(
                    user_to=agent_email,
                    notification_type="Reaction",
                    message=f"{customer_name} replied on ticket #{self.name}: {plain_preview}",
                    reference_ticket=self.name,
                    user_from=customer,
                )
        except Exception:
            frappe.log_error(frappe.get_traceback(), "Agent reply notification error")

    def _create_customer_status_notification(self, old_status, new_status):
        """Create an in-app notification for the customer when ticket status changes."""
        try:
            customer_email = self.raised_by
            if not customer_email or customer_email in ("Administrator", "Guest", ""):
                return
            changer = frappe.session.user
            if changer == customer_email:
                return
            frappe.get_doc({
                "doctype": "HD Notification",
                "user_from": changer,
                "user_to": customer_email,
                "notification_type": "Ticket Status Change",
                "reference_ticket": self.name,
                "message": f"Your ticket #{self.name} status changed to {new_status}",
                "read": 0,
            }).insert(ignore_permissions=True)
        except Exception:
            frappe.log_error(frappe.get_traceback(), "Customer status in-app notification error")

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
        if getattr(self.flags, "allow_plugin_status_change", False):
            return
        is_feedback_mandatory = frappe.get_cached_value(
            "HD Settings", "HD Settings", "is_feedback_mandatory"
        )
        if (
            self.feedback_rating
            or self.status_category != "Resolved"
            or is_agent()
            or not self.has_agent_replied
            or not is_feedback_mandatory
        ):
            return

        frappe.throw(
            _("Ticket must be resolved with a feedback"), frappe.ValidationError
        )

    def check_update_perms(self):
        if (
            self.is_new()
            or is_agent()
            or not self.via_customer_portal
            or getattr(self.flags, "allow_plugin_status_change", False)
        ):
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
    def assign_agent(self, agent: str):
        # ToDo.after_insert hook (overrides/todo_assignment.py) handles
        # the HD Notification — no need to call notify_agent here.
        assign({"assign_to": [agent], "doctype": "HD Ticket", "name": self.name})

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
    def new_comment(self, content: str, attachments: list[str] = []):
        # Allow the ticket owner (customer) to post public comments, not just agents
        user = frappe.session.user
        is_ticket_owner = self.raised_by == user
        if not is_agent() and not is_ticket_owner:
            frappe.throw(
                _("You are not permitted to add a comment"), frappe.PermissionError
            )
        c = frappe.new_doc("HD Ticket Comment")
        c.commented_by = user
        c.content = content
        c.is_pinned = False
        c.is_internal = False
        c.reference_ticket = self.name
        c.save(ignore_permissions=True)
        for attachment in attachments:
            self.attach_file_with_doc(
                "HD Ticket Comment", c.name, attachment.get("file_url")
            )
        # If a customer posted, notify the assigned agent(s) via the bell
        if is_ticket_owner and not is_agent():
            self._notify_agents_of_customer_reply(content)
        return c.name

    @frappe.whitelist()
    def new_internal_note(self, content: str, attachments: list[str] = []):
        if not is_agent():
            frappe.throw(
                _("You are not permitted to add an internal note"), frappe.PermissionError
            )
        c = frappe.new_doc("HD Ticket Comment")
        c.commented_by = frappe.session.user
        c.content = content
        c.is_pinned = False
        c.is_internal = True
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
        to: str | None = None,
        cc: str | None = None,
        bcc: str | None = None,
        attachments: list[str] = [],
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

        # In-app notification for the customer so the bell lights up
        self._create_customer_reply_notification(message, communication.name)

        _attachments = []

        for attachment in attachments:
            file_doc = frappe.get_doc("File", attachment)
            file_doc.attached_to_name = communication.name
            file_doc.attached_to_doctype = "Communication"
            file_doc.save(ignore_permissions=True)
            self.attach_file_with_doc("HD Ticket", self.name, file_doc.file_url)

            _attachments.append({"file_url": file_doc.file_url})

        if skip_email_workflow or not frappe.db.get_single_value(
            "HD Settings", "enable_reply_email_via_agent"
        ):
            return

        if not sender_email:
            frappe.throw(
                _("Unable to send email. Please setup default outgoing email account.")
            )

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
                in_reply_to=(
                    last_communication.name if last_communication.name else None
                ),
            )
        except Exception as e:
            frappe.throw(_(e))

    @frappe.whitelist()
    # flake8: noqa
    def create_communication_via_contact(
        self, message: str, attachments: list[dict] = [], new_ticket: bool = False
    ):
        if not new_ticket and frappe.db.get_single_value(
            "HD Settings", "enable_reply_email_to_agent"
        ):
            # send email to assigned agents
            self.send_reply_email_to_agent()

        # In-app bell notification for assigned agents when customer replies
        if not new_ticket:
            self._notify_agents_of_customer_reply(message)

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
                subject=_("Ticket #{0}: We've received your request").format(self.name),
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
        self.add_seen()
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

    def get_sla(self):
        return frappe.get_doc("HD Service Level Agreement", {"name": self.sla})

    def is_currently_outside_working_hours(self):
        """Return True if current time is outside this SLA's working hours."""

        sla = self.get_sla()
        current_date = getdate()
        now = now_datetime()

        current_td = timedelta(
            hours=now.hour,
            minutes=now.minute,
            seconds=now.second,
            microseconds=now.microsecond,
        )

        day_name = current_date.strftime("%A")
        Holiday = DocType("HD Holiday")

        # Check holidays for this SLA
        holidays = (
            frappe.qb.from_(Holiday)
            .select(Holiday.holiday_date)
            .where(Holiday.parent == sla.name)
            .run(pluck=True)
        )

        if current_date in holidays:
            return True

        working_hours = sla.get_working_hours()
        # No working hours today
        if day_name not in working_hours:
            return True

        start_time, end_time = working_hours[day_name]

        # Outside working hours
        if not (start_time <= current_td < end_time):
            return True
        return False

    def set_default_status(self):
        if self.is_new():
            self.status = self.default_open_status

    def set_status_category(self):
        """Derive status_category from the linked HD Ticket Status record.

        Always re-derives from the HD Ticket Status table on every save to
        prevent tampered status_category values (e.g. via REST API or
        frappe.set_value()) from bypassing downstream validation guards.

        F-01: Use frappe.get_cached_value() instead of frappe.get_value() to
        avoid an unconditional DB round-trip on every save.  The in-process
        document cache is invalidated whenever an HD Ticket Status record is
        saved *within the same Gunicorn worker process*, so freshly-updated
        values are reflected within the same request.

        NOTE — cross-process cache staleness: frappe.get_cached_value() uses
        an in-process document cache (not a shared cache like Redis).  If an
        HD Ticket Status record is updated in one Gunicorn worker, the other
        workers will continue to serve the old cached value until their own
        cache is invalidated (typically on the next request that touches that
        record in that process).  For the status_category field this is
        acceptable: the worst case is that a worker briefly uses a stale
        category until its next cache invalidation, and set_status_category()
        always re-derives from the cache (never trusts self.status_category),
        so the window is bounded to a single request per worker.

        We still always re-derive (never trust self.status_category) to
        prevent tampered values from bypassing downstream guards.

        F-02: get_cached_value / get_value both return None for two distinct
        conditions: (a) the record does not exist, or (b) the category field
        is empty.  An exists() check disambiguates these so we can raise a
        meaningful, actionable error in each case.

        F-13: When self.status is falsy (empty string or None), clear
        status_category to None so downstream guards never see a stale value
        from a previous save.  Silently preserving the old status_category
        when status is cleared is incorrect — callers that set status="" to
        mean "no status" would see a stale category that bypasses validation.
        """
        if not self.status:
            self.status_category = None
            return

        # F-01: get_cached_value avoids a DB round-trip on the hot save path.
        # Always re-derive — never trust self.status_category.
        new_category = frappe.get_cached_value(
            "HD Ticket Status",
            self.status,
            "category",
        )
        if new_category:
            self.status_category = new_category
        else:
            # F-02: Disambiguate missing record vs. empty category field.
            if frappe.db.exists("HD Ticket Status", self.status):
                # Record exists but category field is blank.
                frappe.throw(
                    _(
                        "Status '{0}' exists but has no category assigned."
                        " Please assign a category to the '{0}' HD Ticket"
                        " Status record before saving this ticket."
                    ).format(self.status),
                    frappe.ValidationError,
                )
            else:
                # Record was deleted or never existed.
                frappe.throw(
                    _(
                        "Status '{0}' is invalid: the corresponding HD Ticket"
                        " Status record no longer exists. Please select a"
                        " valid status."
                    ).format(self.status),
                    frappe.ValidationError,
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
            # if received that means customer has replied
            self.last_customer_response = frappe.utils.now_datetime()
        # If communication is outgoing, it must be a reply from agent
        if c.sent_or_received == "Sent":
            # Ignore system notifications
            if c.communication_type and c.communication_type == "Automated Message":
                return
            # Set first response date if not set already
            self.first_responded_on = (
                self.first_responded_on or frappe.utils.now_datetime()
            )
            self.last_agent_response = frappe.utils.now_datetime()

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
            "columns": (
                customer_portal_columns if show_customer_portal_fields else columns
            ),
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
            elif tag.name == "video":
                tag["embed"] = tag.get("src")

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
    def _set_priority_from_keywords(self):
        """Auto-set priority based on keywords in subject/description.

        Story: Priority Workflow - Set default priorities based on keywords.
        Only applies if priority is not already set.
        """
        if self.priority:
            # Priority already set, don't override
            return

        # Urgent keywords
        urgent_keywords = [
            'urgent', 'critical', 'emergency', 'asap', 'immediately',
            'outage', 'down', 'broken', 'not working', 'crashed',
            'production', 'security breach', 'data loss'
        ]

        # High priority keywords
        high_keywords = [
            'important', 'high priority', 'soon', 'blocking',
            'severe', 'major', 'escalated', 'vip'
        ]

        # Low priority keywords
        low_keywords = [
            'minor', 'cosmetic', 'enhancement', 'feature request',
            'question', 'inquiry', 'feedback', 'suggestion'
        ]

        # Combine subject and description for checking
        text_to_check = (self.subject or '').lower()
        if self.description:
            # Extract text from HTML description
            soup = BeautifulSoup(self.description, 'html.parser')
            text_to_check += ' ' + soup.get_text().lower()

        # Check for urgent keywords
        if any(keyword in text_to_check for keyword in urgent_keywords):
            # Get highest priority (lowest integer_value)
            priorities = frappe.get_all(
                'HD Ticket Priority',
                fields=['name'],
                order_by='integer_value asc',
                limit=1
            )
            if priorities:
                self.priority = priorities[0].name
                return

        # Check for high priority keywords
        if any(keyword in text_to_check for keyword in high_keywords):
            # Get second highest priority
            priorities = frappe.get_all(
                'HD Ticket Priority',
                fields=['name'],
                order_by='integer_value asc',
                limit=2
            )
            if len(priorities) >= 2:
                self.priority = priorities[1].name
                return
            elif priorities:
                self.priority = priorities[0].name
                return

        # Check for low priority keywords
        if any(keyword in text_to_check for keyword in low_keywords):
            # Get lowest priority (highest integer_value)
            priorities = frappe.get_all(
                'HD Ticket Priority',
                fields=['name'],
                order_by='integer_value desc',
                limit=1
            )
            if priorities:
                self.priority = priorities[0].name
                return

        # Default to Medium or system default
        self.priority = DEFAULT_TICKET_PRIORITY

    def _check_priority_escalation(self):
        """Escalate priority for aging tickets.

        Story: Priority Workflow - Add priority escalation after X hours.
        Escalates ticket priority if it's been open for too long without progress.
        """
        if self.status_category in ('Resolved', 'Closed'):
            # Don't escalate resolved/closed tickets
            return

        # Get escalation settings
        escalation_enabled = frappe.db.get_single_value(
            'HD Settings',
            'enable_priority_escalation'
        )

        if not escalation_enabled:
            return

        escalation_hours = frappe.db.get_single_value(
            'HD Settings',
            'priority_escalation_hours'
        ) or 24

        # Calculate ticket age in hours
        ticket_age = now_datetime() - self.creation
        ticket_age_hours = ticket_age.total_seconds() / 3600

        if ticket_age_hours < escalation_hours:
            # Not old enough to escalate
            return

        # Get current priority details
        current_priority = frappe.get_cached_doc('HD Ticket Priority', self.priority)

        # Find next higher priority (lower integer_value)
        results = frappe.db.get_list(
            'HD Ticket Priority',
            filters=[['integer_value', '<', current_priority.integer_value]],
            fields=['name'],
            order_by='integer_value desc',
            limit=1
        )
        next_priority = results[0].name if results else None

        if next_priority and next_priority != self.priority:
            old_priority = self.priority
            self.priority = next_priority

            # Log the escalation
            comment = frappe.get_doc({
                'doctype': 'Comment',
                'comment_type': 'Info',
                'reference_doctype': 'HD Ticket',
                'reference_name': self.name,
                'content': f'Priority auto-escalated from {old_priority} to {next_priority} after {int(ticket_age_hours)} hours'
            })
            comment.insert(ignore_permissions=True)

            frappe.msgprint(
                _('Ticket priority escalated from {0} to {1} due to age').format(
                    old_priority, next_priority
                ),
                alert=True
            )


CAREVERSE_BRAND = "Careverse"
CAREVERSE_CARE_TEAM = "Careverse Care Team"


def _is_careverse_viewer(user):
    return bool(
        frappe.db.exists("HD Team Member", {"parent": CAREVERSE_CARE_TEAM, "user": user})
    )


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

    if doc.get("brand") == CAREVERSE_BRAND and _is_careverse_viewer(user):
        return True

    if doc.get("_assign", None):
        try:
            assignees = json.loads(doc._assign)
            if user in assignees:
                return True
        except:
            pass

    # Use the same hierarchical scope logic as permission_query
    from .team_hierarchy import get_scoped_teams_for_agent, _LEGACY_FALLBACK

    scoped = get_scoped_teams_for_agent(user)

    if scoped is True:
        # L2 National: sees all tickets
        return True

    if scoped is not _LEGACY_FALLBACK:
        # Hierarchical mode: ticket must belong to one of the agent's scoped teams
        if not scoped:
            return False
        return doc.get("agent_group") in scoped

    # Legacy flat-team fallback
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
    from .team_hierarchy import get_scoped_teams_for_agent

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

    if _is_careverse_viewer(user):
        query += " OR (`tabHD Ticket`.brand = {b})".format(b=frappe.db.escape(CAREVERSE_BRAND))

    teams = get_agents_team()

    if show_tickets_without_team:
        query += " OR (`tabHD Ticket`.agent_group is null OR `tabHD Ticket`.agent_group = '')"

    # If agent belongs to the team which has ignore_permission set to 1.
    # that means this team can see all the tickets without any restriction,
    # even the other team's tickets.
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

    # --- Hierarchical visibility (County support tier model) ---
    # get_scoped_teams_for_agent returns:
    #   True              → L2 National: user sees ALL tickets (no restriction)
    #   _LEGACY_FALLBACK  → no support levels configured → use legacy filter below
    #   list              → restricted to these teams (L0 / L1 / L3)
    from .team_hierarchy import _LEGACY_FALLBACK

    scoped = get_scoped_teams_for_agent(user)

    if scoped is True:
        # L2 National: unrestricted — no WHERE clause needed
        return

    if scoped is not _LEGACY_FALLBACK:
        # Hierarchical mode: restrict to the computed team scope
        query += (
            " OR (JSON_SEARCH(`tabHD Ticket`._assign, 'all', {user}) IS NOT NULL)".format(
                user=frappe.db.escape(user)
            )
        )
        if not scoped:
            # Agent is in no teams — no additional team-based tickets
            return query
        scoped_str = ", ".join(frappe.db.escape(t) for t in scoped)
        query += f" OR (`tabHD Ticket`.agent_group in ({scoped_str}))"
        return query

    # --- Legacy flat-team behaviour (no support levels configured) ---
    query += (
        " OR (JSON_SEARCH(`tabHD Ticket`._assign, 'all', {user}) IS NOT NULL)".format(
            user=frappe.db.escape(user)
        )
    )

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


@contextmanager
def _autoclose_savepoint(ticket):
    """Context manager that wraps one auto-close iteration in a named savepoint.

    On success the savepoint is released.  On ValidationError (expected failure
    modes: checklist guards, DoesNotExist, stale references) the savepoint is
    rolled back and a WARNING is logged — these are not bugs.  On any other
    exception the savepoint is rolled back and frappe.log_error() is called so
    on-call is alerted, but the cron batch continues.

    Defensive design:
      F-01 — frappe.db.rollback() calls are wrapped in try/except so that a DB
              connection failure (e.g. "MySQL server has gone away") in the
              rollback itself does not kill the cron batch.
      F-02 — frappe.log_error() is deferred until AFTER the savepoint scope.
              Inside the savepoint, the Error Log document would be rolled back
              with the savepoint, silently losing the record.  Capturing the
              traceback and logging it after the try/except ensures the write
              lands in the post-rollback transaction committed by the caller.
              The log call itself is also guarded so a still-broken connection
              falls back to the Python logger instead of propagating (F-01).
    """
    _sp = f"sp_autoclose_{ticket}"
    frappe.db.savepoint(_sp)
    _pending_log = None  # (title, message) captured for post-savepoint logging
    try:
        yield
        frappe.db.release_savepoint(_sp)
    except frappe.ValidationError as exc:
        # F-01: defensive rollback — connection may be dead after the exception.
        try:
            frappe.db.rollback(save_point=_sp)
        except Exception as _rb_exc:  # noqa: BLE001
            # F-03: log rollback failures so they are not silently swallowed.
            try:
                frappe.logger().warning(
                    f"Auto-close: savepoint rollback failed for ticket {ticket}: {_rb_exc}"
                )
            except Exception:  # noqa: BLE001
                pass  # last resort — nothing more we can do
        # F-02: guard the warning call itself — if the connection is dead the
        # logger call could also fail; swallow so the cron batch continues.
        try:
            frappe.logger().warning(
                f"Auto-close skipped ticket {ticket} (validation): {exc}"
            )
        except Exception:  # noqa: BLE001
            pass  # best-effort; logger may fail if connection is dead
    except Exception:  # noqa: BLE001
        # F-01: defensive rollback — if this IS a connection failure, swallow it.
        try:
            frappe.db.rollback(save_point=_sp)
        except Exception as _rb_exc:  # noqa: BLE001
            # F-03: log rollback failures so they are not silently swallowed.
            try:
                frappe.logger().warning(
                    f"Auto-close: savepoint rollback failed for ticket {ticket}: {_rb_exc}"
                )
            except Exception:  # noqa: BLE001
                pass  # last resort — nothing more we can do
        # F-02: capture traceback now but defer frappe.log_error() until the
        # block below (outside the savepoint scope) so the Error Log document
        # is committed by the caller's frappe.db.commit(), not rolled back.
        _pending_log = (
            f"Auto-close failed for ticket {ticket}",
            frappe.get_traceback(),
        )
    # F-02: write Error Log AFTER savepoint scope — the savepoint has already
    # been rolled back above, so this write goes into the post-rollback
    # transaction and will be committed by the caller's frappe.db.commit().
    # F-01: guard the write itself in case the connection is still broken.
    if _pending_log:
        try:
            frappe.log_error(title=_pending_log[0], message=_pending_log[1])
        except Exception:  # noqa: BLE001
            # Last-resort fallback when DB is unreachable — at least emit to log.
            # F-01 fix: guard this call too; if the logger itself raises we must
            # not propagate — this is an absolute last resort.
            try:
                frappe.logger().error(
                    _pending_log[0]
                    + "\n"
                    + (str(_pending_log[1]) if _pending_log[1] is not None else "")
                )
            except Exception:  # noqa: BLE001
                pass  # absolute last resort — nothing more we can do


def escalate_ticket_priorities():
    """Hourly scheduler: auto-escalate ticket priority after prolonged agent inactivity.

    Checks HD Settings for:
      enable_priority_escalation  — master toggle
      priority_escalation_hours   — hours of no agent response before first escalation
      priority_escalation_repeat_hours — re-escalate every N more hours (0 = once only)

    Logic:
      - Only open tickets (not Resolved/Closed) are considered.
      - "Inactivity" is measured from last_agent_response (falls back to creation).
      - Priority is bumped one level up (lower integer_value = higher priority).
      - Already-at-top tickets are skipped.
      - Redis dedup key per ticket prevents re-firing within the same inactivity window.
      - An internal comment is added to the ticket for auditability.
      - The assigned agent receives a realtime notification.
    """
    settings = frappe.db.get_value(
        "HD Settings",
        "HD Settings",
        ["enable_priority_escalation", "priority_escalation_hours", "priority_escalation_repeat_hours"],
        as_dict=True,
    )
    if not settings or not settings.get("enable_priority_escalation"):
        return

    inactivity_hours = int(settings.get("priority_escalation_hours") or 24)
    repeat_hours = int(settings.get("priority_escalation_repeat_hours") or 0)

    cutoff = add_to_date(now_datetime(), hours=-inactivity_hours)

    open_tickets = frappe.get_all(
        "HD Ticket",
        filters={
            "status": ["not in", ["Resolved", "Closed"]],
        },
        or_filters=[
            ["last_agent_response", "<", cutoff],
            ["last_agent_response", "is", "not set"],
        ],
        fields=["name", "priority", "assigned_to", "subject", "last_agent_response", "creation"],
    )

    escalated = 0
    for t in open_tickets:
        try:
            _maybe_escalate_priority(t, inactivity_hours, repeat_hours, cutoff)
            escalated += 1
        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                f"Auto-priority escalation failed for ticket {t.name}",
            )

    if escalated:
        frappe.logger().info(f"Auto-priority escalation: {escalated} tickets processed")


def _maybe_escalate_priority(ticket_data, inactivity_hours: int, repeat_hours: int, cutoff) -> None:
    """Attempt to escalate a single ticket's priority. No-ops if already at top or recently fired."""
    if not ticket_data.priority:
        return

    redis_key = f"helpdesk:auto_prio_esc:{ticket_data.name}"

    # Check dedup: if already fired within this window, skip unless repeat is enabled
    if frappe.cache().get(redis_key):
        return

    current_prio = frappe.db.get_value(
        "HD Ticket Priority", ticket_data.priority, "integer_value"
    )
    if current_prio is None:
        return

    # Lower integer_value = higher priority. Find the next step up.
    next_priority = frappe.db.get_value(
        "HD Ticket Priority",
        filters=[["integer_value", "<", current_prio]],
        fieldname="name",
        order_by="integer_value desc",
    )

    if not next_priority:
        # Already at the highest priority — nothing to do
        return

    # Compute how long the ticket has been inactive
    last_response = ticket_data.last_agent_response or ticket_data.creation
    inactive_seconds = (now_datetime() - last_response).total_seconds()
    inactive_hours = int(inactive_seconds / 3600)

    old_priority = ticket_data.priority

    # Apply the priority bump directly on the DB row (avoids triggering all hooks)
    frappe.db.set_value("HD Ticket", ticket_data.name, "priority", next_priority)

    # Internal audit comment
    note_content = _(
        "Priority auto-escalated from <strong>{0}</strong> to <strong>{1}</strong> "
        "after {2} hours of inactivity (no agent response)."
    ).format(old_priority, next_priority, inactive_hours)
    frappe.get_doc({
        "doctype": "HD Ticket Comment",
        "reference_ticket": ticket_data.name,
        "commented_by": "Administrator",
        "content": note_content,
        "is_internal": 1,
        "is_pinned": 0,
    }).insert(ignore_permissions=True)

    # Realtime notification to assigned agent
    if ticket_data.assigned_to:
        frappe.publish_realtime(
            "escalation_notification",
            {
                "ticket": ticket_data.name,
                "message": _(
                    "Ticket #{0} priority escalated: {1} → {2} (inactive {3}h)"
                ).format(ticket_data.name, old_priority, next_priority, inactive_hours),
                "team": None,
            },
            user=ticket_data.assigned_to,
            after_commit=True,
        )

    frappe.db.commit()  # nosemgrep

    # Mark dedup. TTL = repeat window (or inactivity window if no repeat)
    ttl_hours = repeat_hours if repeat_hours > 0 else inactivity_hours
    frappe.cache().set_value(redis_key, 1, expires_in_sec=ttl_hours * 3600)


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
        # _autoclose_savepoint wraps each iteration in a named savepoint so a
        # failure on one ticket only rolls back that iteration's DB changes —
        # previously-committed closures stay intact.  Logging is handled inside
        # the CM (WARNING for ValidationError, ERROR for unexpected exceptions).
        with _autoclose_savepoint(ticket):
            doc = frappe.get_doc("HD Ticket", ticket)
            doc.status = "Closed"
            # F-02: do NOT set ignore_validate=True here — that bypassed the
            # validate_checklist_before_resolution() guard entirely.  Auto-close
            # must respect the same validation rules as a manual close.
            doc.save(ignore_permissions=True)
        try:
            frappe.db.commit()  # nosemgrep — persist close or error log
        except Exception:  # noqa: BLE001
            # F-02 fix: commit failed — likely a dead DB connection.  Attempt a
            # rollback to leave the connection in a clean state, then break the
            # loop.  Continuing would cause every subsequent ticket to fail too,
            # creating a silent failure cascade (the exact bug this fixes).
            try:
                frappe.logger().error(
                    f"Auto-close: frappe.db.commit() failed for ticket {ticket}; "
                    "aborting remaining tickets to prevent failure cascade"
                )
            except Exception:  # noqa: BLE001
                pass  # last resort — nothing more we can do
            try:
                frappe.db.rollback()
            except Exception:  # noqa: BLE001
                pass  # ignore rollback errors — connection may already be dead
            break  # dead connection — abort remaining tickets


COUNTY_TEAM_MAP = {
    # Coast Region
    "Mombasa": "Coast Region", "Kwale": "Coast Region", "Kilifi": "Coast Region",
    "Tana River": "Coast Region", "Lamu": "Coast Region", "Taita-Taveta": "Coast Region",
    # Central Region
    "Nyandarua": "Central Region", "Nyeri": "Central Region", "Kirinyaga": "Central Region",
    "Murang'a": "Central Region", "Kiambu": "Central Region",
    # Nairobi
    "Nairobi": "Nairobi Metropolitan",
    # Eastern Region
    "Meru": "Eastern Region", "Tharaka-Nithi": "Eastern Region", "Embu": "Eastern Region",
    "Kitui": "Eastern Region", "Machakos": "Eastern Region", "Makueni": "Eastern Region",
    "Garissa": "Eastern Region", "Wajir": "Eastern Region", "Mandera": "Eastern Region",
    "Marsabit": "Eastern Region", "Isiolo": "Eastern Region",
    # Western Region
    "Kakamega": "Western Region", "Vihiga": "Western Region",
    "Bungoma": "Western Region", "Busia": "Western Region",
    # Nyanza Region
    "Siaya": "Nyanza Region", "Kisumu": "Nyanza Region", "Homa Bay": "Nyanza Region",
    "Migori": "Nyanza Region", "Kisii": "Nyanza Region", "Nyamira": "Nyanza Region",
    # Rift Valley North
    "Turkana": "Rift Valley North", "West Pokot": "Rift Valley North",
    "Samburu": "Rift Valley North", "Trans-Nzoia": "Rift Valley North",
    "Uasin Gishu": "Rift Valley North", "Elgeyo-Marakwet": "Rift Valley North",
    "Baringo": "Rift Valley North",
    # Rift Valley South
    "Nandi": "Rift Valley South", "Laikipia": "Rift Valley South", "Nakuru": "Rift Valley South",
    "Narok": "Rift Valley South", "Kajiado": "Rift Valley South",
    "Kericho": "Rift Valley South", "Bomet": "Rift Valley South",
}


def _get_team_for_county(county):
    """Return the L1 regional team for a given county name."""
    return COUNTY_TEAM_MAP.get(county)


def _get_default_national_team():
    """Return the name of the best-available fallback national team.

    Story County-2: when no HD Facility Mapping exists for a user's facility,
    assign the ticket to the 'L2 - National' support level team.
    Looks for a team whose support_level has the highest level_order (≥ 2).
    Returns None if no suitable team is found.
    """
    # Find support level with level_order >= 2 (national or higher)
    national_level = frappe.db.get_value(
        "HD Support Level",
        filters=[["level_order", ">=", 2]],
        fieldname="name",
        order_by="level_order asc",
    )
    if not national_level:
        return None

    # Find a team assigned to that support level
    team = frappe.db.get_value(
        "HD Team",
        filters={"support_level": national_level},
        fieldname="name",
        order_by="creation asc",
    )
    return team
