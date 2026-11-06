from collections.abc import Iterator
from datetime import datetime, time, timedelta
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
    to_timedelta,
)

from helpdesk.utils import capture_event, get_context, is_json_valid, publish_event


class HDServiceLevelAgreement(Document):
    doctype_ticket = "HD Ticket"

    def validate(self):
        self.validate_default_sla()
        self.validate_priorities()
        self.validate_support_and_resolution()
        self.validate_condition()
        self.warn_removed_priorities()
        self.warn_detach_on_untick("default_sla", _("Default SLA turned off"))
        self.warn_detach_on_untick("enabled", _("SLA disabled"))

    def validate_priorities(self):
        self.validate_priority_defaults()
        self.validate_response_and_resolution_time()
        self.validate_unique_priorities()

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

    def warn_removed_priorities(self):
        """Warn when dropping a priority that open tickets on this SLA still use."""
        before = self.get_doc_before_save()
        if not before:
            return
        removed = {p.priority for p in before.priorities} - {
            p.priority for p in self.priorities
        }
        for priority in removed:
            count = self.count_open_tickets(priority=priority)
            if not count:
                continue
            frappe.msgprint(
                _(
                    "{0} open tickets use priority {1}. They lose this SLA the next time they are updated."
                ).format(count, priority),
                title=_("Priority in use"),
                indicator="orange",
            )

    def warn_detach_on_untick(self, fieldname: str, title: str):
        """Warn when unticking a checkbox that keeps tickets attached to this policy."""
        if not self.has_value_changed(fieldname) or self.get(fieldname):
            return
        count = self.count_open_tickets()
        if not count:
            return
        frappe.msgprint(
            _(
                "{0} open tickets will lose this SLA the next time they are updated, unless another policy matches them."
            ).format(count),
            title=title,
            indicator="orange",
        )

    def count_open_tickets(self, **filters) -> int:
        """Tickets still on the clock, so Paused counts too — they detach as well."""
        return frappe.db.count(
            self.doctype_ticket,
            {"sla": self.name, "status_category": ["!=", "Resolved"], **filters},
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
            self.validate_break(support_and_resolution)

            support_days.append(support_and_resolution.workday)

        # Check for repeated workday
        # flake8: noqa
        if not len(set(support_days)) == len(support_days):
            repeated_days = get_repeated(support_days)
            frappe.throw(_("Workday {0} has been repeated.").format(repeated_days))

    def validate_break(self, workday: Document):
        """A break is optional, but needs both ends and must sit inside the workday."""
        if not workday.break_start and not workday.break_end:
            return
        if not (workday.break_start and workday.break_end):
            frappe.throw(
                _(
                    "Set both Break Start and Break End in row <u>{0}</u>, or neither."
                ).format(workday.idx)
            )
        times = [
            to_timedelta(workday.get(fieldname))
            for fieldname in ("start_time", "break_start", "break_end", "end_time")
        ]
        if not all(earlier < later for earlier, later in zip(times, times[1:])):
            frappe.throw(
                _(
                    "Break must start after Start Time, end after it starts and end before End Time in row <u>{0}</u>."
                ).format(workday.idx)
            )

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

    def validate_condition(self):
        if self.condition:
            try:
                temp_doc = frappe.new_doc(self.doctype_ticket)
                frappe.safe_eval(self.condition, None, get_context(temp_doc))
            except Exception as e:
                frappe.throw(
                    _("The assignment condition '{0}' is invalid: {1}").format(
                        self.condition, str(e)
                    )
                )

        if self.condition_json and not is_json_valid(self.condition_json):
            frappe.throw(
                _("The assignment condition json '{0}' is invalid: {1}").format(
                    self.condition_json,
                    "Condition format should be like this e.g [['status','==','open']], it's recommended to use portal view to create conditions.",
                )
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
        self.set_default_priority(doc)
        self.start_clock(doc)
        self.handle_doc_status(doc)
        self.handle_targets(doc)
        self.set_failed_by(doc)
        self.handle_agreement_status(doc)

    def set_default_priority(self, doc: Document):
        doc.priority = doc.priority or self.default_priority

    def start_clock(self, doc: Document):
        """Stamp the moment targets are counted from. Written once, when the SLA
        attaches, which may be long after the ticket was raised."""
        if not doc.service_level_agreement_creation:
            doc.service_level_agreement_creation = now_datetime()

    def handle_doc_status(self, doc: Document):
        if not doc.is_valid_status_transition():
            return
        self.set_first_response_time(doc)
        self.set_hold_time(doc)
        self.set_resolution_time(doc)

    def set_first_response_time(self, doc: Document):
        start_at = doc.service_level_agreement_creation
        end_at = doc.first_responded_on
        if not start_at or not end_at:
            return
        doc.first_response_time = self.calc_elapsed_time(start_at, end_at)

    def set_resolution_time(self, doc: Document):
        """Business-hours duration to resolve. The date itself is stamped by the
        ticket, which does not need an SLA to know when it was resolved."""
        if not doc.resolution_date:
            return
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
        paused_since = doc.on_hold_since
        if not paused_since and doc.status_category != "Resolved":
            # time spent resolved counts as hold only when the ticket is reopened
            paused_since = doc_old.get("resolution_date")
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

    def set_failed_by(self, doc: Document):
        """Against current targets, so an SLA change re-measures them."""
        doc.first_response_failed_by = self.get_time_past(
            doc.response_by, doc.first_responded_on
        )
        doc.resolution_failed_by = self.get_time_past(
            doc.resolution_by, doc.resolution_date
        )

    def get_time_past(self, due, end) -> int | None:
        if not (due and end) or get_datetime(end) <= get_datetime(due):
            return None
        return self.calc_elapsed_time(due, end)

    def set_response_by(self, doc: Document):
        doc.response_by = self.calc_time(
            doc.service_level_agreement_creation, doc.priority, "response_time"
        )

    def set_resolution_by(self, doc: Document):
        total_hold_time = doc.total_hold_time or 0
        doc.resolution_by = self.calc_time(
            doc.service_level_agreement_creation,
            doc.priority,
            "resolution_time",
            hold_time=total_hold_time,
        )

    def handle_agreement_status(self, doc: Document):
        is_failed = self.is_first_response_failed(doc) or self.is_resolution_failed(doc)

        if is_failed:
            doc.agreement_status = "Failed"
        elif doc.on_hold_since:
            doc.agreement_status = "Paused"
        elif not doc.first_responded_on:
            doc.agreement_status = "First Response Due"
        elif self.apply_sla_for_resolution and not doc.resolution_date:
            doc.agreement_status = "Resolution Due"
        else:
            doc.agreement_status = "Fulfilled"

    def is_first_response_failed(self, doc: Document):
        if not doc.first_responded_on:
            return get_datetime(doc.response_by) < self.get_active_ticket_time(doc)
        return get_datetime(doc.response_by) < get_datetime(doc.first_responded_on)

    def is_resolution_failed(self, doc: Document):
        if not self.apply_sla_for_resolution or not doc.resolution_by:
            return
        if not doc.resolution_date:
            return get_datetime(doc.resolution_by) < self.get_active_ticket_time(doc)
        return get_datetime(doc.resolution_by) < get_datetime(doc.resolution_date)

    def get_active_ticket_time(self, doc: Document):
        """Hold time is credited only on resume, so an on-hold ticket is measured
        against when it went on hold."""
        return get_datetime(doc.on_hold_since) if doc.on_hold_since else now_datetime()

    def calc_time(
        self,
        start_at: str,
        priority: str,
        target: Literal["response_time", "resolution_time"],
        hold_time: float = 0,
    ) -> datetime:
        """
        When the target is expected to be met, counting only working time:
        holidays, non-workdays, time outside working hours and breaks are skipped.
        Hold time (in seconds) is added to the resolution target.
        """
        cursor = get_datetime(start_at)
        remaining = self.get_priorities()[priority].get(target) or 0
        if target == "resolution_time":
            remaining += hold_time
        if not remaining:
            return cursor
        for span_start, span_end in self.iter_working_spans(cursor):
            if span_end <= cursor:
                continue
            cursor = max(span_start, cursor)
            available = (span_end - cursor).total_seconds()
            if remaining <= available:
                return cursor + timedelta(seconds=remaining)
            remaining -= available

    def calc_elapsed_time(self, start_time, end_time) -> int:
        """Working seconds between start_time and end_time, per calc_time's calendar."""
        # whole seconds, so durations stay integers
        start_time = get_datetime(start_time).replace(microsecond=0)
        end_time = get_datetime(end_time).replace(microsecond=0)
        total_seconds = 0
        for span_start, span_end in self.iter_working_spans(start_time, end_time):
            overlap = min(span_end, end_time) - max(span_start, start_time)
            total_seconds += max(overlap.total_seconds(), 0)
        return int(total_seconds)

    def iter_working_spans(
        self, from_datetime: datetime, to_datetime: datetime | None = None
    ) -> Iterator[tuple[datetime, datetime]]:
        """
        Yield each working interval as (start, end) datetimes, day by day from
        from_datetime's date, skipping holidays and non-workdays. Endless
        without to_datetime, so callers stop once they have what they need.
        """
        holidays = set(self.get_holidays())
        workdays = self.get_workdays()
        day = getdate(from_datetime)
        last_day = getdate(to_datetime) if to_datetime else None
        while not last_day or day <= last_day:
            workday = workdays.get(get_weekdays()[day.weekday()])
            if workday and day not in holidays:
                midnight = datetime.combine(day, time())
                for start, end in self.get_working_intervals(workday):
                    yield midnight + start, midnight + end
            day += timedelta(days=1)

    def get_working_intervals(
        self, workday: Document
    ) -> list[tuple[timedelta, timedelta]]:
        """
        A workday's working time as (start, end) offsets from midnight: one
        interval, or two around its break. The only place that reads a workday's
        hours, so every SLA calculation skips the break the same way.
        """
        start, end = to_timedelta(workday.start_time), to_timedelta(workday.end_time)
        if not (workday.break_start and workday.break_end):
            return [(start, end)]
        return [
            (start, to_timedelta(workday.break_start)),
            (to_timedelta(workday.break_end), end),
        ]

    def get_working_hours(self) -> dict[str, list[tuple[timedelta, timedelta]]]:
        """Working intervals per weekday name, for is_working_time."""
        return {
            row.workday: self.get_working_intervals(row)
            for row in self.support_and_resolution
        }

    def is_working_time(self, date_time: datetime, working_hours: dict) -> bool:
        """True when date_time falls in one of its weekday's working intervals."""
        day_of_week = get_weekdays()[date_time.weekday()]
        time_of_day = timedelta(
            hours=date_time.hour, minutes=date_time.minute, seconds=date_time.second
        )
        return any(
            start <= time_of_day < end
            for start, end in working_hours.get(day_of_week, [])
        )

    def get_next_working_day_start(self, from_date):
        """Start of the first working day after from_date, skipping holidays."""
        working_hours = self.get_working_hours()
        holidays = set(self.get_holidays())
        # a year of lookahead is plenty; None means the calendar has no working day
        for offset in range(1, 366):
            next_date = getdate(add_to_date(from_date, days=offset, as_datetime=True))
            day_name = next_date.strftime("%A")
            if day_name in working_hours and next_date not in holidays:
                # the day's start, not the end of its break
                return get_datetime(next_date) + working_hours[day_name][0][0]
        return None

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

    def after_insert(self):
        capture_event("sla_created")


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
