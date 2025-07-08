from datetime import timedelta
from typing import Literal

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import (
    add_to_date,
    cint,
    get_datetime,
    get_weekdays,
    getdate,
    now_datetime,
    time_diff_in_seconds,
    to_timedelta,
)

from helpdesk.utils import get_context, publish_event


class HDServiceLevelAgreement(Document):
    doctype_ticket = "HD Ticket"

    def validate(self):
        self.validate_default_sla()
        self.validate_priorities()
        self.validate_support_and_resolution()
        self.validate_condition()  # Looks okay but check again

    def validate_priorities(self):
        self.validate_priority_defaults()
        self.validate_response_and_resolution_time()
        self.validate_unique_priorities()
        self.validate_all_priorities()

    # check if we have more than one default priority
    def validate_priority_defaults(self):
        if sum(d.default_priority for d in self.priorities) > 1:
            frappe.throw(_("You cannot set more than one Default Priority."))

    # Check if response and resolution time is set for every priority
    def validate_response_and_resolution_time(self):
        for priority in self.priorities:
            if not priority.response_time:
                frappe.throw(
                    _("Set Response Time for Priority {0} in row {1}.").format(
                        priority.priority, priority.idx
                    )
                )

            if self.apply_sla_for_resolution:
                if not priority.resolution_time:
                    frappe.throw(
                        _("Set Resolution Time for Priority {0} in row {1}.").format(
                            priority.priority, priority.idx
                        )
                    )

                response = cint(priority.response_time)
                resolution = cint(priority.resolution_time)
                if response > resolution:
                    frappe.throw(
                        _(
                            "Response Time for {0} priority in row {1} can't be greater"
                            " than Resolution Time."
                        ).format(priority.priority, priority.idx)
                    )

    def validate_unique_priorities(self):
        priorities = [d.priority for d in self.priorities]
        if len(priorities) != len(set(priorities)):
            repeated_priority = get_repeated(priorities)
            frappe.throw(_("Priority {0} has been repeated.").format(repeated_priority))

    def validate_all_priorities(self):
        all_priorities = frappe.get_all("HD Ticket Priority", pluck="name")
        sla_priorities = [p.priority for p in self.priorities]

        for priority in all_priorities:
            if priority not in sla_priorities:
                frappe.msgprint(
                    _("Priority <u>{0}</u> must be included in the SLA {1}.").format(
                        priority, self.name
                    )
                )

    def validate_support_and_resolution(self):
        week = get_weekdays()
        support_days = []

        for support_and_resolution in self.support_and_resolution:

            if to_timedelta(support_and_resolution.start_time) >= to_timedelta(
                support_and_resolution.end_time
            ):
                frappe.throw(
                    _(
                        "Start Time can't be greater than or equal to End Time in row <u>{0}</u>."
                    ).format(support_and_resolution.idx)
                )

            support_days.append(support_and_resolution.workday)

        # Check for repeated workday
        # flake8: noqa
        if not len(set(support_days)) == len(support_days):
            repeated_days = get_repeated(support_days)
            frappe.throw(_("Workday {0} has been repeated.").format(repeated_days))

    def validate_default_sla(self):
        default_sla_exists = frappe.db.exists(
            self.doctype,
            {
                "default_sla": True,
                "name": ["!=", self.name],
            },
        )

        if default_sla_exists and self.default_sla:
            frappe.db.set_value(self.doctype, default_sla_exists, "default_sla", False)
            frappe.msgprint(
                _(
                    "Setting <strong>{0}</strong> as the default SLA removes <strong>{1}</strong> as the default SLA. You’ll need to add a condition in <strong>{1}</strong> for the SLA to work."
                ).format(self.name, default_sla_exists)
            )

        if not self.default_sla and not default_sla_exists:
            frappe.throw(
                _(
                    "You must set one SLA as Default. Please check the Default SLA option."
                )
            )

        if self.has_value_changed("enabled") and not self.enabled and self.default_sla:
            frappe.throw(_("You cannot disable the default SLA."))

    def validate_condition(self):
        if not self.condition:
            return
        try:
            temp_doc = frappe.new_doc(self.doctype_ticket)
            frappe.safe_eval(self.condition, None, get_context(temp_doc))
        except Exception as e:
            frappe.throw(
                _("The Condition '{0}' is invalid: {1}").format(self.condition, str(e))
            )

    def before_save(self):
        # set default priority
        try:
            self.default_priority = next(
                d.priority for d in self.priorities if d.default_priority
            )
        except Exception:
            frappe.throw(_("Select a Default Priority."))

    def apply(self, doc: Document):
        self.handle_new(doc)
        self.handle_status(doc)
        self.handle_targets(doc)
        self.handle_agreement_status(doc)
        self.validate_all_priorities()

    def handle_new(self, doc: Document):
        if not doc.is_new():
            return
        creation = doc.service_level_agreement_creation or now_datetime()
        doc.service_level_agreement_creation = creation
        doc.priority = doc.priority or self.default_priority

    def handle_status(self, doc: Document):
        if doc.is_new() or not doc.has_value_changed("status"):
            return
        self.set_first_response_time(doc)
        self.set_resolution_date(doc)
        self.set_hold_time(doc)

    def set_first_response_time(self, doc: Document):
        start_at = doc.service_level_agreement_creation
        end_at = doc.first_responded_on
        if not start_at or not end_at:
            return
        doc.first_response_time = self.calc_elapsed_time(start_at, end_at)

    def set_resolution_date(self, doc: Document):
        fullfill_on = [row.status for row in self.sla_fulfilled_on]
        next_state = doc.get("status")
        is_fulfilled = next_state in fullfill_on
        if not is_fulfilled:
            doc.resolution_date = None
            doc.resolution_time = None
            return
        doc.resolution_date = now_datetime()
        start_at = doc.service_level_agreement_creation
        end_at = doc.resolution_date
        time_took = self.calc_elapsed_time(start_at, end_at)
        time_hold = doc.total_hold_time or 0
        time_took_effective = time_took - time_hold
        doc.resolution_time = time_took_effective

    def set_hold_time(self, doc: Document):
        pause_on = [row.status for row in self.pause_sla_on]
        doc_old = doc.get_doc_before_save()
        prev_state = doc_old.get("status")
        next_state = doc.get("status")
        was_paused = prev_state in pause_on
        is_paused = next_state in pause_on
        paused_since = doc.on_hold_since or doc_old.get("resolution_date")
        if is_paused and not was_paused:
            doc.response_by = doc.resolution_by if doc.first_responded_on else None
            doc.resolution_date = None
            doc.resolution_by = None
            doc.resolution_time = None
            doc.on_hold_since = now_datetime()
        else:
            doc.on_hold_since = None
        if is_paused or not paused_since:
            return
        doc.on_hold_since = None
        curr_val = time_diff_in_seconds(now_datetime(), paused_since)
        doc.total_hold_time = (doc.total_hold_time or 0) + curr_val

    def handle_targets(self, doc: Document):
        self.set_response_by(doc)
        self.set_resolution_by(doc)

    def set_response_by(self, doc: Document):
        start = doc.service_level_agreement_creation
        doc.response_by = self.calc_time(start, doc.priority, "response_time")

    def set_resolution_by(self, doc: Document):
        total_hold_time = doc.total_hold_time or 0
        start = add_to_date(
            doc.service_level_agreement_creation,
            seconds=total_hold_time,
            as_datetime=True,
        )
        doc.resolution_by = self.calc_time(start, doc.priority, "resolution_time")

    def reset_resolution_metrics(self, doc: Document):
        pause_on = [row.status for row in self.pause_sla_on]
        fullfill_on = [row.status for row in self.sla_fulfilled_on]
        prev_state = doc.get_doc_before_save().get("status")
        next_state = doc.get("status")
        was_paused = prev_state in pause_on
        was_fulfilled = prev_state in fullfill_on
        is_paused = next_state in pause_on
        is_fulfilled = next_state in fullfill_on
        is_open = not is_paused and not is_fulfilled
        if is_open and (was_paused or was_fulfilled):
            return
        doc.response_date = None
        doc.resolution_date = None
        doc.user_resolution_time = None

    def handle_agreement_status(self, doc: Document):
        is_failed = self.is_first_response_failed(doc) or self.is_resolution_failed(doc)
        options = {
            "Fulfilled": True,
            "Resolution Due": self.apply_sla_for_resolution and not doc.resolution_date,
            "First Response Due": not doc.first_responded_on,
            "Failed": is_failed,
            "Paused": doc.on_hold_since,
        }
        for status in options:
            if options[status]:
                doc.agreement_status = status

    def is_first_response_failed(self, doc: Document):
        if not doc.first_responded_on:
            return get_datetime(doc.response_by) < now_datetime()
        return get_datetime(doc.response_by) < get_datetime(doc.first_responded_on)

    def is_resolution_failed(self, doc: Document):
        if not self.apply_sla_for_resolution or not doc.resolution_by:
            return
        if not doc.resolution_date:
            return get_datetime(doc.resolution_by) < now_datetime()
        return get_datetime(doc.resolution_by) < get_datetime(doc.resolution_date)

    def calc_time(
        self,
        start_at: str,
        priority: str,
        target: Literal["response_time", "resolution_time"],
    ):
        res = get_datetime(start_at)
        priorities = self.get_priorities()

        if priority not in priorities:
            frappe.throw(
                _("Please add {0} priority in {1} SLA").format(priority, self.name)
            )
        priority = priorities[priority]

        time_needed = priority.get(target, 0)
        holidays = self.get_holidays()
        weekdays = get_weekdays()
        workdays = self.get_workdays()
        while time_needed:
            today = res
            today_day = getdate(today)
            today_weekday = weekdays[today.weekday()]
            is_workday = today_weekday in workdays
            is_holiday = today_day in holidays
            if is_holiday or not is_workday:
                res = add_to_date(res, days=1, as_datetime=True)
                continue
            today_workday = workdays[today_weekday]
            now_in_seconds = time_diff_in_seconds(today, today_day)
            start_time = max(today_workday.start_time.total_seconds(), now_in_seconds)
            till_start_time = max(start_time - now_in_seconds, 0)
            end_time = max(today_workday.end_time.total_seconds(), now_in_seconds)
            time_left = max(end_time - start_time, 0)
            if not time_left:
                res = getdate(add_to_date(res, days=1, as_datetime=True))
                continue
            time_taken = min(time_needed, time_left)
            time_needed -= time_taken
            time_required = till_start_time + time_taken
            res = add_to_date(res, seconds=time_required, as_datetime=True)
        return res

    def get_working_days(self) -> dict[str, dict]:
        workdays = []
        for row in self.support_and_resolution:
            workdays.append(row.workday)
        return workdays

    def get_working_hours(self) -> dict[str, dict]:
        res = {}
        for row in self.support_and_resolution:
            res[row.workday] = (row.start_time, row.end_time)
        return res

    def is_working_time(self, date_time, working_hours):
        day_of_week = get_weekdays()[date_time.weekday()]
        start_time, end_time = working_hours.get(day_of_week, (0, 0))
        date_time = timedelta(
            hours=date_time.hour, minutes=date_time.minute, seconds=date_time.second
        )
        return start_time <= date_time < end_time

    def calc_elapsed_time(self, start_time, end_time) -> float:
        """
        Get took from start to end, excluding non-working hours

        :param start_at: Date at which calculation starts
        :param end_at: Date at which calculation ends
        :return: Number of seconds
        """
        start_time = get_datetime(start_time)
        end_time = get_datetime(end_time)
        holiday_list = []
        working_day_list = self.get_working_days()
        working_hours = self.get_working_hours()

        total_seconds = 0
        current_time = start_time

        while current_time < end_time:
            in_holiday_list = current_time.date() in holiday_list
            not_in_working_day_list = (
                get_weekdays()[current_time.weekday()] not in working_day_list
            )
            if (
                in_holiday_list
                or not_in_working_day_list
                or not self.is_working_time(current_time, working_hours)
            ):
                current_time += timedelta(minutes=1)
                continue
            total_seconds += 1
            current_time += timedelta(minutes=1)
        return total_seconds * 60

    def get_holidays(self):
        res = []
        if not self.holiday_list:
            return res
        holiday_list = frappe.get_doc("HD Service Holiday List", self.holiday_list)
        for row in holiday_list.holidays:
            res.append(row.holiday_date)
        return res

    def get_priorities(self):
        """
        Return priorities related info as a dict. With `priority` as key
        """
        res = {}
        for row in self.priorities:
            res[row.priority] = row
        return res

    def get_workdays(self) -> dict[str, dict]:
        """
        Return workdays related info as a dict. With `workday` as key
        """
        res = {}
        for row in self.support_and_resolution:
            res[row.workday] = row
        return res

    # temporary, will remove once sla goes to frontend
    def before_insert(self):
        user = frappe.session.user
        user_onboarding_status = frappe.get_value("User", user, "onboarding_status")
        if not user_onboarding_status:
            return

        user_onboarding_status = frappe.parse_json(user_onboarding_status)
        if not user_onboarding_status:
            return
        hd_onboarding_steps = user_onboarding_status.get("helpdesk_onboarding_status")
        if not hd_onboarding_steps:
            return

        sla_onboarding_status = {}
        for step in hd_onboarding_steps:
            if step.get("name") == "setup_sla":
                sla_onboarding_status = step
                break

        if not sla_onboarding_status:
            return
        if sla_onboarding_status.get("completed"):
            return

        frappe.publish_realtime("update_sla_status", user=frappe.session.user)

    def on_trash(self):
        self.handle_default_sla_deletion()

    def handle_default_sla_deletion(self):
        if not self.default_sla:
            return
        default_sla_exists = frappe.db.exists(
            self.doctype,
            {
                "default_sla": True,
                "name": ["!=", self.name],
            },
        )
        if default_sla_exists:
            return
        else:
            frappe.throw(
                _(
                    "Cannot delete the default SLA. At least one SLA must be marked as default."
                )
            )


def get_repeated(values):
    unique_list = []
    diff = []
    for value in values:
        if value not in unique_list:
            unique_list.append(str(value))
        else:
            if value not in diff:
                diff.append(str(value))
    return " ".join(diff)
