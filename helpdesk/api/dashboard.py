from datetime import datetime, timedelta

import frappe


@frappe.whitelist()
def get_all():
	return [
		ticket_statuses(),
		avg_first_response_time(),
		ticket_types(),
		new_tickets(),
		resolution_within_sla(),
		ticket_activity(),
		ticket_priority(),
	]


def ticket_statuses():
	date_7_days_ago = datetime.now() - timedelta(days=7)
	filters = {"creation": [">=", date_7_days_ago.strftime("%Y-%m-%d")]}

	res = frappe.db.get_list(
		"HD Ticket",
		fields=["count(name) as value", "status as name"],
		filters=filters,
		group_by="status",
	)

	return {
		"title": "Status",
		"is_chart": True,
		"chart_type": "Pie",
		"data": res,
	}


def avg_first_response_time():
	average_resolution_time = float(0.0)
	date_7_days_ago = datetime.now() - timedelta(days=7)
	filters = {
		"creation": [">=", date_7_days_ago.strftime("%Y-%m-%d")],
		"resolution_time": ["not like", ""],
	}

	ticket_list = frappe.get_list(
		"HD Ticket",
		fields=["name", "resolution_time"],
		filters=filters,
	)

	for ticket in ticket_list:
		average_resolution_time += ticket.resolution_time

	res = "Not enough data"

	if ticket_list:
		h = round((((average_resolution_time) / len(ticket_list)) / 3600), 1)
		res = f"{h} Hours"

	return {
		"title": "Avg First Response Time",
		"is_chart": False,
		"data": res,
	}


def ticket_types():
	date_7_days_ago = datetime.now() - timedelta(days=7)
	filters = {"creation": [">=", date_7_days_ago.strftime("%Y-%m-%d")]}

	res = frappe.db.get_list(
		"HD Ticket",
		fields=["count(name) as value", "ticket_type as name"],
		filters=filters,
		group_by="ticket_type",
	)

	return {
		"title": "Type",
		"is_chart": True,
		"chart_type": "Pie",
		"data": res,
	}


def new_tickets():
	date_7_days_ago = datetime.now() - timedelta(days=7)
	filters = {"creation": [">=", date_7_days_ago.strftime("%Y-%m-%d")]}

	res = frappe.db.get_list(
		"HD Ticket",
		fields=["COUNT(name) as value", "DATE_FORMAT(creation, '%d/%m/%Y') as name"],
		filters=filters,
		group_by="DATE(creation)",
		order_by="DATE(creation)",
	)

	return {
		"title": "New Tickets",
		"is_chart": True,
		"chart_type": "Line",
		"data": res,
	}


def resolution_within_sla():
	date_7_days_ago = datetime.now() - timedelta(days=7)
	filters = {
		"creation": [">=", date_7_days_ago.strftime("%Y-%m-%d")],
		"status": "Closed",
	}

	ticket_list = frappe.get_list(
		"HD Ticket",
		filters=filters,
		fields=["name", "agreement_status", "sla"],
	)

	count = 0

	for ticket in ticket_list:
		if ticket.agreement_status == "Fulfilled":
			count = count + 1

	res = "0%"

	if count:
		resolution_within_sla_percentage = (count / len(ticket_list)) * 100
		resolution_within_sla_percentage = round(resolution_within_sla_percentage, 1)

		res = str(resolution_within_sla_percentage) + "%"

	return {
		"title": "Resolution Within SLA",
		"is_chart": False,
		"data": res,
	}


def ticket_activity():
	date_7_days_ago = datetime.now() - timedelta(days=7)
	filters = {"creation": [">=", date_7_days_ago.strftime("%Y-%m-%d")]}

	res = frappe.db.get_list(
		"HD Ticket Activity",
		fields=["COUNT(name) as value", "DATE_FORMAT(creation, '%d/%m/%Y') as name"],
		filters=filters,
		group_by="DATE(creation)",
		order_by="DATE(creation)",
	)

	return {
		"title": "Activity",
		"is_chart": True,
		"chart_type": "Line",
		"data": res,
	}


def ticket_priority():
	date_7_days_ago = datetime.now() - timedelta(days=7)
	filters = {"creation": [">=", date_7_days_ago.strftime("%Y-%m-%d")]}

	res = frappe.db.get_list(
		"HD Ticket",
		fields=["count(name) as value", "priority as name"],
		filters=filters,
		group_by="priority",
	)

	return {
		"title": "Priority",
		"is_chart": True,
		"chart_type": "Pie",
		"data": res,
	}
