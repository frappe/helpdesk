from typing import Literal

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import (
	add_to_date,
	get_datetime,
	get_weekdays,
	getdate,
	now_datetime,
	time_diff_in_seconds,
	to_timedelta,
)

from helpdesk.utils import get_context


class HDServiceLevelAgreement(Document):
	def validate(self):
		self.validate_priorities()  # To refactor
		self.validate_support_and_resolution()  # To refactor
		self.validate_condition()  # Looks okay but check again

	def validate_priorities(self):
		priorities = []

		for priority in self.priorities:
			# Check if response and resolution time is set for every priority
			if not priority.response_time:
				frappe.throw(
					_("Set Response Time for Priority {0} in row {1}.").format(
						priority.priority, priority.idx
					)
				)

			if self.apply_sla_for_resolution:
				if not priority.resolution_time:
					frappe.throw(
						_("Set Response Time for Priority {0} in row {1}.").format(
							priority.priority, priority.idx
						)
					)

				response = priority.response_time
				resolution = priority.resolution_time
				if response > resolution:
					frappe.throw(
						_(
							"Response Time for {0} priority in row {1} can't be greater"
							" than Resolution Time."
						).format(priority.priority, priority.idx)
					)

			priorities.append(priority.priority)

		# Check if repeated priority
		if not len(set(priorities)) == len(priorities):
			repeated_priority = get_repeated(priorities)
			frappe.throw(_("Priority {0} has been repeated.").format(repeated_priority))

		# set default priority from priorities
		try:
			self.default_priority = next(
				d.priority for d in self.priorities if d.default_priority
			)
		except Exception:
			frappe.throw(_("Select a Default Priority."))

	def validate_support_and_resolution(self):
		week = get_weekdays()
		support_days = []

		for support_and_resolution in self.support_and_resolution:
			support_days.append(support_and_resolution.workday)
			support_and_resolution.idx = week.index(support_and_resolution.workday) + 1

			if to_timedelta(support_and_resolution.start_time) >= to_timedelta(
				support_and_resolution.end_time
			):
				frappe.throw(
					_(
						"Start Time can't be greater than or equal to End Time for {0}."
					).format(support_and_resolution.workday)
				)

		# Check for repeated workday
		if not len(set(support_days)) == len(support_days):
			repeated_days = get_repeated(support_days)
			frappe.throw(_("Workday {0} has been repeated.").format(repeated_days))

	def validate_condition(self):
		if not self.condition:
			return
		try:
			temp_doc = frappe.new_doc(self.document_type)
			frappe.safe_eval(self.condition, None, get_context(temp_doc))
		except Exception:
			frappe.throw(_("The Condition '{0}' is invalid").format(self.condition))

	# What?
	def get_hd_service_level_agreement_priority(self, priority):
		priority = frappe.get_doc(
			"HD Service Level Priority", {"priority": priority, "parent": self.name}
		)

		return frappe._dict(
			{
				"priority": priority.priority,
				"response_time": priority.response_time,
				"resolution_time": priority.resolution_time,
			}
		)

	def on_trash(self):
		if self.service_level == "Default":
			text = _("The Default HD Service Level Agreement cannot be deleted")
			frappe.throw(text, frappe.PermissionError)

	def apply(self, doc: Document):
		self.handle_new(doc)
		self.handle_targets(doc)
		self.handle_status(doc)
		self.handle_agreement_status(doc)

	def handle_new(self, doc: Document):
		if not doc.is_new():
			return
		creation = doc.service_level_agreement_creation or now_datetime()
		doc.service_level_agreement_creation = creation
		doc.priority = doc.priority or self.default_priority

	def handle_status(self, doc: Document):
		if doc.is_new() or not doc.has_value_changed("status"):
			return
		self.set_first_responded_at(doc)
		self.set_resolution_date(doc)
		self.set_hold_time(doc)

	def set_first_responded_at(self, doc: Document):
		next_state = doc.get("status")
		pause_on = [row.status for row in self.pause_sla_on]
		is_paused = next_state in pause_on
		if is_paused:
			doc.first_responded_on = doc.first_responded_on or now_datetime()

	def set_resolution_date(self, doc: Document):
		fullfill_on = [row.status for row in self.sla_fulfilled_on]
		prev_state = doc.get_doc_before_save().get("status")
		next_state = doc.get("status")
		was_fulfilled = prev_state in fullfill_on
		is_fulfilled = next_state in fullfill_on
		if is_fulfilled and not was_fulfilled:
			doc.resolution_date = now_datetime()
		if not is_fulfilled:
			doc.resolution_date = None

	def set_hold_time(self, doc: Document):
		pause_on = [row.status for row in self.pause_sla_on]
		prev_state = doc.get_doc_before_save().get("status")
		next_state = doc.get("status")
		was_paused = prev_state in pause_on
		is_paused = next_state in pause_on
		paused_since = doc.resolution_date or doc.on_hold_since
		if is_paused and not was_paused:
			doc.on_hold_since = now_datetime()
			self.reset_targets(doc)
		else:
			doc.on_hold_since = None
		if is_paused or not paused_since:
			return
		doc.on_hold_since = None
		curr_val = time_diff_in_seconds(now_datetime(), paused_since)
		doc.total_hold_time = (doc.total_hold_time or 0) + curr_val

	def handle_targets(self, doc: Document):
		doc.response_by = self.calc_time(doc, "response_time")
		doc.resolution_by = self.calc_time(doc, "resolution_time")

	def reset_targets(self, doc: Document):
		doc.response_by = doc.resolution_by if doc.first_responded_on else None
		doc.resolution_by = doc.resolution_by if doc.resolution_date else None

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
		if self.apply_sla_for_resolution:
			if not doc.get("first_responded_on"):
				doc.agreement_status = "First Response Due"
			elif not doc.get("resolution_date"):
				doc.agreement_status = "Resolution Due"
			elif get_datetime(doc.get("resolution_date")) <= get_datetime(
				doc.get("resolution_by")
			):
				doc.agreement_status = "Fulfilled"
			else:
				doc.agreement_status = "Overdue"
		else:
			if not doc.get("first_responded_on"):
				doc.agreement_status = "First Response Due"
			elif get_datetime(doc.get("first_responded_on")) <= get_datetime(
				doc.get("response_by")
			):
				doc.agreement_status = "Fulfilled"
			else:
				doc.agreement_status = "Overdue"

	def calc_time(
		self, doc: Document, target: Literal["response_time", "resolution_time"]
	):
		res = get_datetime(doc.service_level_agreement_creation or doc.creation)
		priority = self.get_priorities()[doc.priority]
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

	def get_holidays(self):
		holiday_list = frappe.get_doc("HD Service Holiday List", self.holiday_list)
		return holiday_list.holidays

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
