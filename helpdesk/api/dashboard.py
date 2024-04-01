from datetime import datetime, timedelta

import frappe
from frappe.query_builder.functions import Count
from frappe.utils.caching import redis_cache
from frappe import _, db
from frappe.utils import today, add_days, getdate, get_user_date_format
from frappe.utils.data import date_diff


@frappe.whitelist()
def get_all():
	return [
		avg_first_response_time(),
		resolution_within_sla(),
		my_tickets(),
		ticket_statuses(),
		new_tickets(),
		ticket_types(),
		ticket_activity(),
		ticket_priority(),
		get_user_time_entries(),
	]


@redis_cache(ttl=60 * 5)
def ticket_statuses():
	thirty_days_ago = datetime.now() - timedelta(days=30)
	filters = {"creation": [">=", thirty_days_ago.strftime("%Y-%m-%d")]}

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


@redis_cache(ttl=60 * 5)
def avg_first_response_time():
	average_resolution_time = float(0.0)
	thirty_days_ago = datetime.now() - timedelta(days=30)
	filters = {
		"creation": [">=", thirty_days_ago.strftime("%Y-%m-%d")],
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
		"title": "Avg. first response time",
		"is_chart": False,
		"data": res,
	}


@redis_cache(ttl=60 * 5)
def ticket_types():
	thirty_days_ago = datetime.now() - timedelta(days=30)
	filters = {"creation": [">=", thirty_days_ago.strftime("%Y-%m-%d")]}

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


@redis_cache(ttl=60 * 5)
def new_tickets():
	thirty_days_ago = datetime.now() - timedelta(days=30)
	filters = {"creation": [">=", thirty_days_ago.strftime("%Y-%m-%d")]}

	res = frappe.db.get_list(
		"HD Ticket",
		fields=["COUNT(name) as value", "DATE(creation) as name"],
		filters=filters,
		group_by="DATE(creation)",
		order_by="DATE(creation)",
	)

	return {
		"title": "New tickets",
		"is_chart": True,
		"chart_type": "Line",
		"data": res,
	}


@redis_cache(ttl=60 * 5)
def resolution_within_sla():
	thirty_days_ago = datetime.now() - timedelta(days=30)
	filters = {
		"creation": [">=", thirty_days_ago.strftime("%Y-%m-%d")],
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
		"title": "Resolution within SLA",
		"is_chart": False,
		"data": res,
	}


@redis_cache(ttl=60 * 5)
def ticket_activity():
	thirty_days_ago = datetime.now() - timedelta(days=30)
	filters = {"creation": [">=", thirty_days_ago.strftime("%Y-%m-%d")]}

	res = frappe.db.get_list(
		"HD Ticket Activity",
		fields=["COUNT(name) as value", "DATE(creation) as name"],
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


@redis_cache(ttl=60 * 5)
def ticket_priority():
	thirty_days_ago = datetime.now() - timedelta(days=30)
	filters = {"creation": [">=", thirty_days_ago.strftime("%Y-%m-%d")]}

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


@redis_cache(ttl=60 * 5, user=True)
def my_tickets():
	QBTicket = frappe.qb.DocType("HD Ticket")
	like_str = f"%{frappe.session.user}%"
	like_query = QBTicket._assign.like(like_str)

	res = (
		frappe.qb.from_(QBTicket)
		.select(Count(QBTicket.name, "count"))
		.select(QBTicket.status)
		.where(like_query)
		.where(QBTicket.status.isin(["Open", "Replied"]))
		.groupby(QBTicket.status)
		.run(as_dict=True)
	)

	def map_row(row):
		return f"{row['count']} {row['status']}"

	res = " / ".join(map(map_row, res)).lower()

	return {
		"title": "My tickets",
		"is_chart": False,
		"data": res,
	}


@redis_cache(ttl=60 * 5, user=True)
def get_user_time_entries():
	frappe.utils.logger.set_log_level("DEBUG")
	logger = frappe.logger("dashboard", allow_site=True, file_count=50)

	end_date = getdate(today())
	start_date = add_days(end_date, -6)  # Last 30 days, including today
	user = frappe.session.user
	user_date_format = get_user_date_format()
	python_date_format = user_date_format.replace('dd', '%d').replace('mm', '%m').replace('yyyy', '%Y')
	# Assuming "HD Ticket Time Tracking" has "agent" (user email) and "duration" (in seconds)
	data = db.sql("""
		SELECT
		DATE(start_time) as date, SUM(duration) as total_duration
		FROM
		`tabHD Ticket Time Tracking`
		WHERE
		agent = %s AND
		DATE(start_time) BETWEEN %s AND %s
		GROUP BY
		DATE(start_time)
		ORDER BY
		DATE(start_time)
		""", (user, start_date, end_date), as_dict=1)
	logger.debug('Data is: '+str(data))
	logger.debug('User is: '+str(user))
	start_date = getdate(start_date)
	# Fill missing days with 0 duration
	result = []
	for n in range((end_date - start_date).days + 1):
		single_date = start_date + timedelta(days=n)
		formatted_date = single_date.strftime(user_date_format)
		# Find duration for the current date or use 0 if not found
		duration = next((item['total_duration'] for item in data if item['date'] == single_date), 0)
		result.append({
			'name': single_date.strftime(python_date_format),  # Formatting here for output only
			'value': round(duration / 3600, 5)  # Convert seconds to hours
		})
	logger.debug('result is: '+str(result))
	return {
		"title": "Hours recorded last 7 days",
		"is_chart": True,
		"chart_type": "Line",
		"data": result,
	}