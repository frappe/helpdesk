# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import json

import frappe
from frappe import _, scrub
from frappe.utils import flt
from six import iteritems


def execute(filters=None):
	return TicketSummary(filters).run()


class TicketSummary(object):
	def __init__(self, filters=None):
		self.filters = frappe._dict(filters or {})

	def run(self):
		self.get_columns()
		self.get_data()
		self.get_chart_data()
		self.get_report_summary()

		return self.columns, self.data, None, self.chart, self.report_summary

	def get_columns(self):
		self.columns = []

		if self.filters.based_on == "Contact":
			self.columns.append(
				{
					"label": _("Contact"),
					"options": "Contact",
					"fieldname": "contact",
					"fieldtype": "Link",
					"width": 200,
				}
			)

		elif self.filters.based_on == "Assigned To":
			self.columns.append(
				{
					"label": _("User"),
					"fieldname": "user",
					"fieldtype": "Link",
					"options": "User",
					"width": 200,
				}
			)

		elif self.filters.based_on == "Ticket Type":
			self.columns.append(
				{
					"label": _("Ticket Type"),
					"fieldname": "ticket_type",
					"fieldtype": "Link",
					"options": "HD Ticket Type",
					"width": 200,
				}
			)

		elif self.filters.based_on == "Ticket Priority":
			self.columns.append(
				{
					"label": _("Ticket Priority"),
					"fieldname": "priority",
					"fieldtype": "Link",
					"options": "HD Ticket Priority",
					"width": 200,
				}
			)

		self.statuses = ["Open", "Replied", "Resolved", "Closed"]
		for status in self.statuses:
			self.columns.append(
				{"label": _(status), "fieldname": scrub(status), "fieldtype": "Int", "width": 80}
			)

		self.columns.append(
			{
				"label": _("Total Ticket"),
				"fieldname": "total_tickets",
				"fieldtype": "Int",
				"width": 100,
			}
		)

		self.sla_status_map = {
			"SLA Failed": "failed",
			"SLA Fulfilled": "fulfilled",
			"SLA Ongoing": "ongoing",
		}

		for label, fieldname in self.sla_status_map.items():
			self.columns.append(
				{"label": _(label), "fieldname": fieldname, "fieldtype": "Int", "width": 100}
			)

		self.metrics = [
			"Avg First Response Time",
			"Avg Response Time",
			"Avg Hold Time",
			"Avg Resolution Time",
			"Avg User Resolution Time",
		]

		for metric in self.metrics:
			self.columns.append(
				{
					"label": _(metric),
					"fieldname": scrub(metric),
					"fieldtype": "Duration",
					"width": 170,
				}
			)

	def get_data(self):
		self.get_tickets()
		self.get_rows()

	def get_tickets(self):
		filters = self.get_common_filters()
		self.field_map = {
			"Contact": "contact",
			"Ticket Type": "ticket_type",
			"Ticket Priority": "priority",
			"Assigned To": "_assign",
		}

		self.entries = frappe.db.get_all(
			"HD Ticket",
			fields=[
				self.field_map.get(self.filters.based_on),
				"name",
				"opening_date",
				"status",
				"avg_response_time",
				"first_response_time",
				"total_hold_time",
				"user_resolution_time",
				"resolution_time",
				"agreement_status",
			],
			filters=filters,
		)

	def get_common_filters(self):
		filters = {}
		filters["opening_date"] = ("between", [self.filters.from_date, self.filters.to_date])

		if self.filters.get("assigned_to"):
			filters["_assign"] = ("like", "%" + self.filters.get("assigned_to") + "%")

		for entry in ["status", "priority", "contact", "ticket_type"]:
			if self.filters.get(entry):
				filters[entry] = self.filters.get(entry)

		return filters

	def get_rows(self):
		self.data = []
		self.get_summary_data()

		for entity, data in iteritems(self.ticket_summary_data):
			if self.filters.based_on == "Contact":
				row = {"contact": entity}
			elif self.filters.based_on == "Assigned To":
				row = {"user": entity}
			elif self.filters.based_on == "Ticket Type":
				row = {"ticket_type": entity}
			elif self.filters.based_on == "Ticket Priority":
				row = {"priority": entity}

			for status in self.statuses:
				count = flt(data.get(status, 0.0))
				row[scrub(status)] = count

			row["total_tickets"] = data.get("total_tickets", 0.0)

			for sla_status in self.sla_status_map.values():
				value = flt(data.get(sla_status), 0.0)
				row[sla_status] = value

			for metric in self.metrics:
				value = flt(data.get(scrub(metric)), 0.0)
				row[scrub(metric)] = value

			self.data.append(row)

	def get_summary_data(self):
		self.ticket_summary_data = frappe._dict()

		for d in self.entries:
			status = d.status
			agreement_status = scrub(d.agreement_status)

			if self.filters.based_on == "Assigned To":
				if d._assign:
					for entry in json.loads(d._assign):
						self.ticket_summary_data.setdefault(entry, frappe._dict()).setdefault(status, 0.0)
						self.ticket_summary_data.setdefault(entry, frappe._dict()).setdefault(
							agreement_status, 0.0
						)
						self.ticket_summary_data.setdefault(entry, frappe._dict()).setdefault(
							"total_tickets", 0.0
						)
						self.ticket_summary_data[entry][status] += 1
						self.ticket_summary_data[entry][agreement_status] += 1
						self.ticket_summary_data[entry]["total_tickets"] += 1

			else:
				field = self.field_map.get(self.filters.based_on)
				value = d.get(field)
				if not value:
					value = _("Not Specified")

				self.ticket_summary_data.setdefault(value, frappe._dict()).setdefault(status, 0.0)
				self.ticket_summary_data.setdefault(value, frappe._dict()).setdefault(
					agreement_status, 0.0
				)
				self.ticket_summary_data.setdefault(value, frappe._dict()).setdefault(
					"total_tickets", 0.0
				)
				self.ticket_summary_data[value][status] += 1
				self.ticket_summary_data[value][agreement_status] += 1
				self.ticket_summary_data[value]["total_tickets"] += 1

		self.get_metrics_data()

	def get_metrics_data(self):
		ticket = []

		metrics_list = [
			"avg_response_time",
			"avg_first_response_time",
			"avg_hold_time",
			"avg_resolution_time",
			"avg_user_resolution_time",
		]

		for entry in self.entries:
			ticket.append(entry.name)

		field = self.field_map.get(self.filters.based_on)

		if ticket:
			if self.filters.based_on == "Assigned To":
				assignment_map = frappe._dict()
				for d in self.entries:
					if d._assign:
						for entry in json.loads(d._assign):
							for metric in metrics_list:
								self.ticket_summary_data.setdefault(entry, frappe._dict()).setdefault(
									metric, 0.0
								)

							self.ticket_summary_data[entry]["avg_response_time"] += (
								d.get("avg_response_time") or 0.0
							)
							self.ticket_summary_data[entry]["avg_first_response_time"] += (
								d.get("first_response_time") or 0.0
							)
							self.ticket_summary_data[entry]["avg_hold_time"] += (
								d.get("total_hold_time") or 0.0
							)
							self.ticket_summary_data[entry]["avg_resolution_time"] += (
								d.get("resolution_time") or 0.0
							)
							self.ticket_summary_data[entry]["avg_user_resolution_time"] += (
								d.get("user_resolution_time") or 0.0
							)

							if not assignment_map.get(entry):
								assignment_map[entry] = 0
							assignment_map[entry] += 1

				for entry in assignment_map:
					for metric in metrics_list:
						self.ticket_summary_data[entry][metric] /= flt(assignment_map.get(entry))

			else:
				data = frappe.db.sql(
					"""
					SELECT
						{0}, AVG(first_response_time) as avg_frt,
						AVG(avg_response_time) as avg_resp_time,
						AVG(total_hold_time) as avg_hold_time,
						AVG(resolution_time) as avg_resolution_time,
						AVG(user_resolution_time) as avg_user_resolution_time
					FROM `tabHD Ticket`
					WHERE
						name IN %(ticket)s
					GROUP BY {0}
				""".format(
						field
					),
					{"ticket": ticket},
					as_dict=1,
				)

				for entry in data:
					value = entry.get(field)
					if not value:
						value = _("Not Specified")

					for metric in metrics_list:
						self.ticket_summary_data.setdefault(value, frappe._dict()).setdefault(metric, 0.0)

					self.ticket_summary_data[value]["avg_response_time"] = (
						entry.get("avg_resp_time") or 0.0
					)
					self.ticket_summary_data[value]["avg_first_response_time"] = (
						entry.get("avg_frt") or 0.0
					)
					self.ticket_summary_data[value]["avg_hold_time"] = (
						entry.get("avg_hold_time") or 0.0
					)
					self.ticket_summary_data[value]["avg_resolution_time"] = (
						entry.get("avg_resolution_time") or 0.0
					)
					self.ticket_summary_data[value]["avg_user_resolution_time"] = (
						entry.get("avg_user_resolution_time") or 0.0
					)

	def get_chart_data(self):
		self.chart = []

		labels = []
		open_tickets = []
		replied_tickets = []
		resolved_tickets = []
		closed_tickets = []

		entity = self.filters.based_on
		entity_field = self.field_map.get(entity)
		if entity == "Assigned To":
			entity_field = "user"

		for entry in self.data:
			labels.append(entry.get(entity_field))
			open_tickets.append(entry.get("open"))
			replied_tickets.append(entry.get("replied"))
			resolved_tickets.append(entry.get("resolved"))
			closed_tickets.append(entry.get("closed"))

		self.chart = {
			"data": {
				"labels": labels[:30],
				"datasets": [
					{"name": "Open", "values": open_tickets[:30]},
					{"name": "Replied", "values": replied_tickets[:30]},
					{"name": "Resolved", "values": resolved_tickets[:30]},
					{"name": "Closed", "values": closed_tickets[:30]},
				],
			},
			"type": "bar",
			"barOptions": {"stacked": True},
		}

	def get_report_summary(self):
		self.report_summary = []

		open_tickets = 0
		replied = 0
		resolved = 0
		closed = 0

		for entry in self.data:
			open_tickets += entry.get("open")
			replied += entry.get("replied")
			resolved += entry.get("resolved")
			closed += entry.get("closed")

		self.report_summary = [
			{"value": open_tickets, "indicator": "Red", "label": _("Open"), "datatype": "Int"},
			{"value": replied, "indicator": "Grey", "label": _("Replied"), "datatype": "Int"},
			{
				"value": resolved,
				"indicator": "Green",
				"label": _("Resolved"),
				"datatype": "Int",
			},
			{"value": closed, "indicator": "Green", "label": _("Closed"), "datatype": "Int"},
		]
