import frappe


DASHBOARD_ITEM_DOCTYPE = "HD Dashboard Item"
SNIPPETS = [
	{
		"title": "New Tickets (7 Days)",
		"enabled": True,
		"is_chart": True,
		"chart_type": "Line",
		"snippet": """from datetime import datetime, timedelta

# Calculate date 7 days ago
date_7_days_ago = datetime.now() - timedelta(days=7)

filters = {
	"creation": [">=", date_7_days_ago.strftime('%Y-%m-%d')]
}

res = frappe.db.get_list(
	"HD Ticket",
	fields=["COUNT(name) as value", "DATE_FORMAT(creation, '%d/%m/%Y') as name"],
	filters = filters,
	group_by="DATE(creation)",
)
		""",
	},
	{
		"title": "Resolution Within SLA",
		"enabled": True,
		"is_chart": False,
		"snippet": """ticket_list = frappe.get_list(
	"HD Ticket",
	filters={"status": "Closed"},
	fields=["name", "agreement_status", "sla"],
)
count = 0

for ticket in ticket_list:
	if ticket.agreement_status == "Fulfilled":
		count = count + 1

if count:
    resolution_within_sla_percentage = (count / len(ticket_list)) * 100
    resolution_within_sla_percentage = round(resolution_within_sla_percentage, 1)
    
    res = str(resolution_within_sla_percentage) + "%"
else:
    res = "0%"
		""",
	},
	{
		"title": "Avg. First Response time",
		"enabled": True,
		"is_chart": False,
		"snippet": """average_resolution_time = float(0.0)
ticket_list = frappe.get_list(
	"HD Ticket",
	fields=["name", "resolution_time"],
	filters={"resolution_time": ["not like", ""]},
)

for ticket in ticket_list:
	average_resolution_time += ticket.resolution_time

if ticket_list:
    h = round((((average_resolution_time) / len(ticket_list)) / 3600), 1)
    res = f"{h} Hours"
else:
    res = "Not enough data"
		""",
	},
	{
		"title": "Type",
		"enabled": True,
		"is_chart": True,
		"chart_type": "Pie",
		"snippet": """
res = frappe.db.get_list(
	"HD Ticket",
	fields=["count(name) as value", "ticket_type as name"],
	group_by="ticket_type",
)
		""",
	},
	{
		"title": "Priority",
		"enabled": True,
		"is_chart": True,
		"chart_type": "Pie",
		"snippet": """
res = frappe.db.get_list(
	"HD Ticket",
	fields=["count(name) as value", "priority as name"],
	group_by="priority",
)
		""",
	},
	{
		"title": "Status",
		"enabled": True,
		"is_chart": True,
		"chart_type": "Pie",
		"snippet": """res = frappe.db.get_list(
	"HD Ticket",
	fields=["count(name) as value", "status as name"],
	group_by="status",
)
		""",
	},
]


def create_dashboard_items():
	for snippet in SNIPPETS:
		filters = {"doctype": DASHBOARD_ITEM_DOCTYPE, "title": snippet["title"]}
		if not frappe.db.exists(filters):
			d = frappe.get_doc(
				{
					"doctype": DASHBOARD_ITEM_DOCTYPE,
					"title": snippet.get("title"),
					"enabled": snippet.get("enabled"),
					"is_chart": snippet.get("is_chart"),
					"chart_type": snippet.get("chart_type", ""),
					"snippet": snippet.get("snippet"),
				}
			)

			d.insert()
