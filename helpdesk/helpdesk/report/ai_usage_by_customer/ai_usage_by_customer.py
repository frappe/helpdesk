# Copyright (c) 2026, Quark Cyber Systems FZC and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	filters = filters or {}
	columns = _get_columns()
	data = _get_data(filters)
	report_summary = _get_report_summary(data)
	return columns, data, None, None, report_summary


def _get_columns():
	return [
		{"label": _("Customer"), "fieldname": "customer_name", "fieldtype": "Data", "width": 200},
		{"label": _("Sessions"), "fieldname": "session_count", "fieldtype": "Int", "width": 100},
		{"label": _("Tool Calls"), "fieldname": "total_tool_calls", "fieldtype": "Int", "width": 110},
		{"label": _("Input Tokens"), "fieldname": "input_tokens", "fieldtype": "Int", "width": 130},
		{"label": _("Output Tokens"), "fieldname": "output_tokens", "fieldtype": "Int", "width": 130},
		{
			"label": _("Total Cost"),
			"fieldname": "cost_usd",
			"fieldtype": "Currency",
			"options": "USD",
			"precision": 4,
			"width": 140,
		},
		{
			"label": _("Avg Cost/Session"),
			"fieldname": "avg_cost",
			"fieldtype": "Currency",
			"options": "USD",
			"precision": 4,
			"width": 150,
		},
	]


def _get_data(filters):
	conditions = []
	params = {}

	if filters.get("from_date"):
		conditions.append("DATE(started_at) >= %(from_date)s")
		params["from_date"] = filters["from_date"]
	if filters.get("to_date"):
		conditions.append("DATE(started_at) <= %(to_date)s")
		params["to_date"] = filters["to_date"]
	if filters.get("status"):
		conditions.append("status = %(status)s")
		params["status"] = filters["status"]

	where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

	rows = frappe.db.sql(
		f"""
		SELECT
			COALESCE(customer_name, 'Unknown') as customer_name,
			COUNT(*) as session_count,
			SUM(total_tool_calls) as total_tool_calls,
			SUM(total_input_tokens) as input_tokens,
			SUM(total_output_tokens) as output_tokens,
			SUM(estimated_cost_usd) as cost_usd
		FROM `tabHDS AI Support Session`
		{where}
		GROUP BY customer_name
		ORDER BY cost_usd DESC
		""",
		params,
		as_dict=True,
	)

	for row in rows:
		row["avg_cost"] = (row["cost_usd"] or 0) / row["session_count"] if row["session_count"] else 0

	return rows


def _get_report_summary(data):
	if not data:
		return []

	return [
		{
			"label": _("Customers"),
			"value": len(data),
			"datatype": "Int",
			"indicator": "Blue",
		},
		{
			"label": _("Total Sessions"),
			"value": sum(r["session_count"] or 0 for r in data),
			"datatype": "Int",
			"indicator": "Blue",
		},
		{
			"label": _("Total Cost"),
			"value": round(sum(r["cost_usd"] or 0 for r in data), 4),
			"datatype": "Currency",
			"indicator": "Green",
		},
	]
