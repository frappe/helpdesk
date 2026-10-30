import frappe
from frappe import _


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart_data(data)
    data = data + get_total_row(data, filters)

    return columns, data, None, chart


def get_columns():
    return [
        {
            "label": _("County"),
            "fieldname": "county",
            "fieldtype": "Link",
            "options": "HD County",
            "width": 150
        },
        {
            "label": _("Total Tickets"),
            "fieldname": "total_tickets",
            "fieldtype": "Int",
            "width": 120
        },
        {
            "label": _("Open"),
            "fieldname": "open",
            "fieldtype": "Int",
            "width": 80
        },
        {
            "label": _("Replied"),
            "fieldname": "replied",
            "fieldtype": "Int",
            "width": 80
        },
        {
            "label": _("Resolved"),
            "fieldname": "resolved",
            "fieldtype": "Int",
            "width": 80
        },
        {
            "label": _("Closed"),
            "fieldname": "closed",
            "fieldtype": "Int",
            "width": 80
        },
        {
            "label": _("Resolved Tickets"),
            "fieldname": "resolution_rate",
            "fieldtype": "Int",
            "width": 130
        },
        {
            "label": _("Avg Response Time (hrs)"),
            "fieldname": "avg_response_time",
            "fieldtype": "Float",
            "width": 180,
            "precision": 2
        },
        {
            "label": _("Assigned Team"),
            "fieldname": "assigned_team",
            "fieldtype": "Data",
            "width": 150
        }
    ]


def get_data(filters):
    conditions = ""
    if filters and filters.get("from_date"):
        conditions += f" AND t.creation >= '{filters.get('from_date')}'"
    if filters and filters.get("to_date"):
        conditions += f" AND t.creation <= '{filters.get('to_date')}'"
    if filters and filters.get("county"):
        conditions += f" AND t.county = '{filters.get('county')}'"

    data = frappe.db.sql(f"""
        SELECT
            t.county,
            COUNT(*) as total_tickets,
            SUM(CASE WHEN t.status = 'Open' THEN 1 ELSE 0 END) as open,
            SUM(CASE WHEN t.status = 'Replied' THEN 1 ELSE 0 END) as replied,
            SUM(CASE WHEN t.status = 'Resolved' THEN 1 ELSE 0 END) as resolved,
            SUM(CASE WHEN t.status = 'Closed' THEN 1 ELSE 0 END) as closed,
            SUM(CASE WHEN t.status IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) as resolution_rate,
            ROUND(
                AVG(
                    CASE
                        WHEN t.first_responded_on IS NOT NULL
                        THEN TIMESTAMPDIFF(HOUR, t.creation, t.first_responded_on)
                        ELSE NULL
                    END
                ),
                2
            ) as avg_response_time,
            -- team.territory is not populated in this deployment, so the
            -- assigned team is derived from actual ticket agent_group data
            -- instead (same approach used by the County Dashboard).
            GROUP_CONCAT(DISTINCT t.agent_group SEPARATOR ', ') as assigned_team
        FROM `tabHD Ticket` t
        WHERE t.county IS NOT NULL AND t.county != '' {conditions}
        GROUP BY t.county
        ORDER BY total_tickets DESC
    """, as_dict=True)

    return data


def get_total_row(data, filters):
    """Grand-total row appended under all the counties: sums the counts,
    recomputes avg_response_time as a true overall average (not an average
    of the per-county averages), and leaves county/assigned_team as labels."""
    if not data:
        return []

    conditions = ""
    if filters and filters.get("from_date"):
        conditions += f" AND t.creation >= '{filters.get('from_date')}'"
    if filters and filters.get("to_date"):
        conditions += f" AND t.creation <= '{filters.get('to_date')}'"
    if filters and filters.get("county"):
        conditions += f" AND t.county = '{filters.get('county')}'"

    totals = frappe.db.sql(f"""
        SELECT
            COUNT(*) as total_tickets,
            SUM(CASE WHEN t.status = 'Open' THEN 1 ELSE 0 END) as open,
            SUM(CASE WHEN t.status = 'Replied' THEN 1 ELSE 0 END) as replied,
            SUM(CASE WHEN t.status = 'Resolved' THEN 1 ELSE 0 END) as resolved,
            SUM(CASE WHEN t.status = 'Closed' THEN 1 ELSE 0 END) as closed,
            SUM(CASE WHEN t.status IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) as resolution_rate,
            ROUND(
                AVG(
                    CASE
                        WHEN t.first_responded_on IS NOT NULL
                        THEN TIMESTAMPDIFF(HOUR, t.creation, t.first_responded_on)
                        ELSE NULL
                    END
                ),
                2
            ) as avg_response_time
        FROM `tabHD Ticket` t
        WHERE t.county IS NOT NULL AND t.county != '' {conditions}
    """, as_dict=True)[0]

    return [{
        "county": _("Total"),
        "total_tickets": totals.total_tickets,
        "open": totals.open,
        "replied": totals.replied,
        "resolved": totals.resolved,
        "closed": totals.closed,
        "resolution_rate": totals.resolution_rate,
        "avg_response_time": totals.avg_response_time,
        "assigned_team": "",
    }]


def get_chart_data(data):
    if not data:
        return None

    # Top 10 counties by ticket volume
    top_counties = data[:10]

    return {
        "data": {
            "labels": [d.county for d in top_counties],
            "datasets": [
                {
                    "name": "Open",
                    "values": [d.open for d in top_counties]
                },
                {
                    "name": "Resolved",
                    "values": [d.resolved for d in top_counties]
                },
                {
                    "name": "Closed",
                    "values": [d.closed for d in top_counties]
                }
            ]
        },
        "type": "bar",
        "colors": ["#FFA00A", "#28A745", "#6C757D"]
    }
