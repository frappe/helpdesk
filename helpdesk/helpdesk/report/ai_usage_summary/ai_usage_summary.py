# Copyright (c) 2026, Quark Cyber Systems FZC and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	filters = filters or {}
	columns = _get_columns()
	data = _get_data(filters)
	chart = _get_chart(data)
	report_summary = _get_report_summary(data)
	return columns, data, None, chart, report_summary


def _get_columns():
	return [
		{"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 110},
		{"label": _("Model"), "fieldname": "model", "fieldtype": "Data", "width": 240},
		{"label": _("Calls"), "fieldname": "call_count", "fieldtype": "Int", "width": 80},
		{"label": _("Input Tokens"), "fieldname": "input_tokens", "fieldtype": "Int", "width": 130},
		{"label": _("Output Tokens"), "fieldname": "output_tokens", "fieldtype": "Int", "width": 130},
		{"label": _("Cache Read"), "fieldname": "cache_read_tokens", "fieldtype": "Int", "width": 120},
		{"label": _("Cache Write"), "fieldname": "cache_write_tokens", "fieldtype": "Int", "width": 120},
		{
			"label": _("Cost (USD)"),
			"fieldname": "cost_usd",
			"fieldtype": "Currency",
			"options": "USD",
			"precision": 4,
			"width": 130,
		},
	]


def _get_data(filters):
	conditions = []
	params = {}

	if filters.get("from_date"):
		conditions.append("DATE(timestamp) >= %(from_date)s")
		params["from_date"] = filters["from_date"]
	if filters.get("to_date"):
		conditions.append("DATE(timestamp) <= %(to_date)s")
		params["to_date"] = filters["to_date"]
	if filters.get("model"):
		conditions.append("model = %(model)s")
		params["model"] = filters["model"]

	where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

	return frappe.db.sql(
		f"""
		SELECT
			DATE(timestamp) as date,
			model,
			COUNT(*) as call_count,
			SUM(input_tokens) as input_tokens,
			SUM(output_tokens) as output_tokens,
			SUM(cache_read_tokens) as cache_read_tokens,
			SUM(cache_write_tokens) as cache_write_tokens,
			SUM(estimated_cost_usd) as cost_usd
		FROM `tabHDS AI Usage Log`
		{where}
		GROUP BY DATE(timestamp), model
		ORDER BY date DESC, model
		""",
		params,
		as_dict=True,
	)


def _get_chart(data):
	if not data:
		return None

	# Group by date, sum costs across all models
	by_date = {}
	for row in data:
		d = str(row["date"])
		by_date[d] = by_date.get(d, 0) + (row["cost_usd"] or 0)

	dates = sorted(by_date.keys())
	costs = [round(by_date[d], 4) for d in dates]

	return {
		"data": {
			"labels": dates,
			"datasets": [{"name": "Cost (USD)", "values": costs}],
		},
		"type": "line",
		"colors": ["#5e64ff"],
	}


def _get_report_summary(data):
	if not data:
		return []

	total_calls = sum(r["call_count"] or 0 for r in data)
	total_input = sum(r["input_tokens"] or 0 for r in data)
	total_output = sum(r["output_tokens"] or 0 for r in data)
	total_cost = sum(r["cost_usd"] or 0 for r in data)
	avg_cost = total_cost / total_calls if total_calls else 0

	return [
		{"label": _("Total Calls"), "value": total_calls, "datatype": "Int", "indicator": "Blue"},
		{"label": _("Input Tokens"), "value": total_input, "datatype": "Int", "indicator": "Grey"},
		{"label": _("Output Tokens"), "value": total_output, "datatype": "Int", "indicator": "Grey"},
		{
			"label": _("Total Cost"),
			"value": round(total_cost, 4),
			"datatype": "Currency",
			"indicator": "Green",
		},
		{
			"label": _("Avg Cost/Call"),
			"value": round(avg_cost, 4),
			"datatype": "Currency",
			"indicator": "Orange",
		},
	]
