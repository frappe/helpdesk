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

from .utils import convert_to_seconds


class HDServiceLevelAgreement(Document):
    doctype_ticket = "HD Ticket"

    def validate(self):
        self.validate_default_sla()
        self.validate_priorities()
        self.validate_support_and_resolution()
        self.validate_condition()

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
        self.handle_doc_status(doc)
        self.handle_targets(doc)
        self.handle_agreement_status(doc)
        self.validate_all_priorities()

    def handle_new(self, doc: Document):
        if not doc.is_new():
            return
        creation = doc.service_level_agreement_creation or now_datetime()
        doc.service_level_agreement_creation = creation
        doc.priority = doc.priority or self.default_priority

    def handle_doc_status(self, doc: Document):
        if doc.is_new() or not doc.has_value_changed("status"):
            return

        was_resolved = (
            doc.get_doc_before_save().get("status_category", None) == "Resolved"
        )
        is_closed = doc.get("status", None) == "Closed"
        if was_resolved and is_closed:
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
        resolved_statuses = (
            frappe.db.get_all(
                "HD Ticket Status", {"category": "Resolved"}, pluck="name"
            )
            or []
        )
        next_state = doc.get("status")
        is_fulfilled = next_state in resolved_statuses
        if not is_fulfilled:
            doc.resolution_date = None
            doc.resolution_time = None
            return
        doc.resolution_date = now_datetime()
        start_at = doc.service_level_agreement_creation
        end_at = doc.resolution_date
        time_took = self.calc_elapsed_time(start_at, end_at)
        time_hold = doc.total_hold_time or 0
        time_took_effective = max(time_took - time_hold, 0)
        doc.resolution_time = time_took_effective

    def set_hold_time(self, doc: Document):
        paused_statuses = (
            frappe.db.get_all("HD Ticket Status", {"category": "Paused"}, pluck="name")
            or []
        )
        doc_old = doc.get_doc_before_save()
        prev_state = doc_old.get("status")
        next_state = doc.get("status")
        was_paused = prev_state in paused_statuses
        is_paused = next_state in paused_statuses
        paused_since = doc.on_hold_since or doc_old.get("resolution_date")
        if is_paused and not was_paused:
            doc.response_by = doc.resolution_by if doc.first_responded_on else None
            doc.resolution_date = None
            doc.resolution_by = None
            doc.resolution_time = None
            doc.on_hold_since = now_datetime()
        elif not is_paused and was_paused:
            doc.on_hold_since = None
        if is_paused or not paused_since:
            return
        doc.on_hold_since = None
        # curr_val = time_diff_in_seconds(now_datetime(), paused_since)
        curr_val = max(self.get_hold_time_diff(paused_since), 0)
        doc.total_hold_time = (doc.total_hold_time or 0) + curr_val

    def get_hold_time_diff(self, paused_since):
        # return time in seconds
        if not paused_since:
            return 0
        return self.calc_elapsed_time(paused_since, now_datetime())

    def handle_targets(self, doc: Document):
        self.set_response_by(doc)
        self.set_resolution_by(doc)

    def set_response_by(self, doc: Document):
        start = doc.service_level_agreement_creation
        doc.response_by = self.calc_time(
            doc.service_level_agreement_creation, doc.priority, "response_time"
        )

    def set_resolution_by(self, doc: Document):
        total_hold_time = doc.total_hold_time or 0
        start = add_to_date(
            doc.service_level_agreement_creation,
            seconds=total_hold_time,
            as_datetime=True,
        )
        doc.resolution_by = self.calc_time(
            doc.service_level_agreement_creation,
            doc.priority,
            "resolution_time",
            hold_time=total_hold_time,
        )

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
        hold_time: float = 0,
    ):
        """
        Considerations:
            - Holidays
            - Workdays
            - Working hours
            - Hold time if target is resolution time (in seconds)

        Returns:
            - DateTime when the target is expected to be met
        """
        result = get_datetime(start_at)
        priorities = self.get_priorities()
        if priority not in priorities:
            frappe.throw(
                _("Please add {0} priority in {1} SLA").format(priority, self.name)
            )
        priority = priorities[priority]
        remaining_target_time = priority.get(
            target, 0
        )  # time for response or resolution in seconds
        holidays = (
            self.get_holidays()
        )  # From Holiday List, returns a list of holiday dates
        days_list = get_weekdays()  # list of weekdays, ["Monday", "Tuesday", ...]
        working_days = (
            self.get_workdays()
        )  # From Working hours table, returns a dict with weekday names as keys and workday objects as values

        if target == "resolution_time":
            # add hold time to remaining target time
            remaining_target_time += hold_time

        while remaining_target_time:
            current_datetime = result
            current_date = getdate(current_datetime)
            current_day = days_list[
                current_datetime.weekday()
            ]  # Returns the current weekday name like Monday or Tuesday etc.

            is_current_day_working = current_day in working_days
            is_holiday = current_date in holidays

            if is_holiday or not is_current_day_working:
                next_date = getdate(add_to_date(result, days=1, as_datetime=True))
                result = next_date
                continue

            current_workday_doc = working_days[
                current_day
            ]  # Get the workday object for the current day
            current_time_in_seconds = time_diff_in_seconds(
                current_datetime, current_date
            )
            start_time = max(
                current_workday_doc.start_time.total_seconds(), current_time_in_seconds
            )
            till_start_time = max(start_time - current_time_in_seconds, 0)
            end_time = max(
                current_workday_doc.end_time.total_seconds(), current_time_in_seconds
            )
            time_left = max(end_time - start_time, 0)
            if not time_left:
                next_date = getdate(add_to_date(result, days=1, as_datetime=True))
                result = next_date
                continue
            time_taken = min(remaining_target_time, time_left)
            remaining_target_time -= time_taken
            time_required = till_start_time + time_taken
            result = add_to_date(result, seconds=time_required, as_datetime=True)
        return result

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

    def calc_elapsed_time(self, start_time, end_time):
        """
        Calculate working time between start_time and end_time, excluding holidays and non-working hours

        :param start_time: Start datetime
        :param end_time: End datetime
        :return: Number of working seconds
        """
        start_time = get_datetime(start_time)
        end_time = get_datetime(end_time)

        if start_time >= end_time:
            return 0

        holidays = set(self.get_holidays())
        workdays = self.get_workdays()

        total_seconds = 0
        current_date = start_time.date()
        end_date = end_time.date()

        while current_date <= end_date:
            # Skip holidays
            if current_date in holidays:
                current_date = add_to_date(current_date, days=1)
                continue

            day_name = get_weekdays()[current_date.weekday()]

            # Skip non-working days
            if day_name not in workdays:
                current_date = add_to_date(current_date, days=1)
                continue

            workday = workdays[day_name]
            work_start_seconds = workday.start_time.total_seconds()
            work_end_seconds = workday.end_time.total_seconds()

            # Calculate day boundaries in seconds
            if current_date == start_time.date():
                # First day - convert start time to seconds since midnight
                start_time_seconds = convert_to_seconds(start_time)
                day_start_seconds = max(start_time_seconds, work_start_seconds)
            else:
                day_start_seconds = work_start_seconds

            if current_date == end_time.date():
                # Last day - convert end time to seconds since midnight
                end_time_seconds = convert_to_seconds(end_time)
                day_end_seconds = min(end_time_seconds, work_end_seconds)
            else:
                day_end_seconds = work_end_seconds

            # adding to final total seconds by end - start
            if day_start_seconds < day_end_seconds:
                total_seconds += day_end_seconds - day_start_seconds

            current_date = add_to_date(current_date, days=1)

        return total_seconds

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
