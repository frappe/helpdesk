import frappe

from helpdesk.utils import agent_only


@frappe.whitelist()
@agent_only
def get_dashboard_data(type, filters=None):
    """
    Get dashboard data based on the type and date range.
    """
    from_date = filters.get("from_date") if filters else None
    to_date = filters.get("to_date") if filters else None
    team = filters.get("team") if filters else None
    agent = filters.get("agent") if filters else None

    if not from_date:
        from_date = frappe.utils.add_days(frappe.utils.nowdate(), -30)
    if not to_date:
        to_date = frappe.utils.nowdate()

    if type == "number_card":
        return get_number_card_data(from_date, to_date, team, agent)
    elif type == "master":
        return get_master_dashboard_data(from_date, to_date)
        print("Master Dashboard Data")
    elif type == "trend":
        print("\n\n", "TREND", "\n\n")


def get_number_card_data(from_date, to_date, team=None, agent=None):
    """
    Get number card data for the dashboard.
    """
    from_date = frappe.utils.add_days(frappe.utils.nowdate(), -30)
    to_date = frappe.utils.nowdate()
    # Remove from and to date after testing

    ticket_chart_data = get_ticket_count(from_date, to_date)
    resolved_tickets = get_resolved_tickets(from_date, to_date)
    sla_fulfilled_count = get_sla_fulfilled_count(from_date, to_date)
    avg_resolution_time = get_avg_resolution_time(from_date, to_date)
    avg_feedback_score = get_avg_feedback_score(from_date, to_date)

    return [
        ticket_chart_data,
        resolved_tickets,
        sla_fulfilled_count,
        avg_resolution_time,
        avg_feedback_score,
    ]


def get_ticket_count(from_date, to_date):
    """
    Get ticket data for the dashboard.
    """
    from_date = frappe.utils.add_days(frappe.utils.nowdate(), -30)
    to_date = frappe.utils.nowdate()
    result = frappe.db.sql(
        """
		SELECT
				COUNT(CASE
					WHEN creation >= %(from_date)s AND creation <= %(to_date)s 
					THEN name
					ELSE NULL
				END) as current_month_tickets,

				COUNT(CASE
					WHEN creation >= %(prev_from_date)s AND creation < %(from_date)s 
					THEN name
					ELSE NULL
				END) as prev_month_tickets
		FROM `tabHD Ticket`
    """,
        {
            "from_date": from_date,
            "to_date": to_date,
            "prev_from_date": frappe.utils.add_months(from_date, -1),
        },
        as_dict=1,
    )

    current_month_tickets = result[0].current_month_tickets or 0
    prev_month_tickets = result[0].prev_month_tickets or 0
    delta_in_percentage = (
        (current_month_tickets - prev_month_tickets) / prev_month_tickets * 100
        if prev_month_tickets
        else 0
    )

    return {
        "title": "Tickets",
        "value": current_month_tickets,
        "delta": delta_in_percentage,
        "deltaSuffix": "%",
        "negativeIsBetter": True,
    }


def get_resolved_tickets(from_date, to_date):
    """
    Get resolved tickets for the dashboard.
    """
    result = frappe.db.sql(
        """
        SELECT 
            COUNT(CASE 
                WHEN creation >= %(from_date)s AND creation <= %(to_date)s AND status IN ('Resolved', 'Closed')
                THEN name 
                ELSE NULL
            END) as current_month_resolved,
            COUNT(CASE 
                WHEN creation >= %(prev_from_date)s AND creation < %(from_date)s AND status IN ('Resolved', 'Closed')
                THEN name 
                ELSE NULL
            END) as prev_month_resolved
        FROM `tabHD Ticket`
    """,
        {
            "from_date": from_date,
            "to_date": to_date,
            "prev_from_date": frappe.utils.add_months(from_date, -1),
        },
        as_dict=1,
    )
    current_month_resolved = result[0].current_month_resolved or 0
    prev_month_resolved = result[0].prev_month_resolved or 0

    delta_in_percentage = (
        (current_month_resolved - prev_month_resolved) / prev_month_resolved * 100
        if prev_month_resolved
        else 0
    )
    return {
        "title": "% Resolved",
        "value": current_month_resolved,
        "suffix": "%",
        "delta": delta_in_percentage,
        "deltaSuffix": "%",
    }


def get_sla_fulfilled_count(from_date, to_date):
    #    "fieldname": "agreement_status",
    # value:"Fulfilled"
    """
    Get the percent of SLA tickets fulfilled for the dashboard.
    """
    result = frappe.db.sql(
        """
        SELECT 
            COUNT(CASE 
                WHEN creation >= %(from_date)s AND creation <= %(to_date)s AND agreement_status = 'Fulfilled'
                THEN name 
                ELSE NULL
            END) as current_month_fulfilled,
            COUNT(CASE 
                WHEN creation >= %(prev_from_date)s AND creation < %(from_date)s AND agreement_status = 'Fulfilled'
                THEN name 
                ELSE NULL
            END) as prev_month_fulfilled
        FROM `tabHD Ticket`
    """,
        {
            "from_date": from_date,
            "to_date": to_date,
            "prev_from_date": frappe.utils.add_months(from_date, -1),
        },
        as_dict=1,
    )
    current_month_fulfilled = result[0].current_month_fulfilled or 0
    prev_month_fulfilled = result[0].prev_month_fulfilled or 0

    delta_in_percentage = (
        (current_month_fulfilled - prev_month_fulfilled) / prev_month_fulfilled * 100
        if prev_month_fulfilled
        else 0
    )
    return {
        "title": "% SLA Fulfilled",
        "value": current_month_fulfilled,
        "suffix": "%",
        "delta": delta_in_percentage,
        "deltaSuffix": "%",
    }


def get_avg_resolution_time(from_date, to_date):
    """
    Get average resolution time for the dashboard.
    """
    from_date = frappe.utils.add_days(frappe.utils.nowdate(), -30)
    to_date = frappe.utils.nowdate()
    result = frappe.db.sql(
        """
        SELECT 
            AVG(CASE 
                WHEN status = 'Resolved' AND creation >= %(from_date)s AND creation <= %(to_date)s
                THEN TIMESTAMPDIFF(DAY, creation, resolution_date)
                ELSE NULL
            END) as current_month_avg,
            AVG(CASE 
                WHEN status = 'Resolved' AND creation >= %(prev_from_date)s AND creation < %(from_date)s
                THEN TIMESTAMPDIFF(DAY, creation, resolution_date)
                ELSE NULL
            END) as prev_month_avg
        FROM `tabHD Ticket`
        WHERE 
            (creation >= %(prev_from_date)s AND creation <= %(to_date)s)
    """,
        {
            "from_date": from_date,
            "to_date": to_date,
            "prev_from_date": frappe.utils.add_months(from_date, -1),
        },
        as_dict=1,
    )
    current_month_avg = result[0].current_month_avg or 0
    prev_month_avg = result[0].prev_month_avg or 0

    delta = current_month_avg - prev_month_avg if prev_month_avg else 0
    return {
        "title": "Avg. Resolution Time",
        "value": current_month_avg,
        "suffix": " days",
        "delta": delta,
        "deltaSuffix": " days",
        "negativeIsBetter": True,
    }


def get_avg_feedback_score(from_date, to_date):
    """
    Get average feedback score for the dashboard.
    """
    from_date = frappe.utils.add_days(frappe.utils.nowdate(), -30)
    to_date = frappe.utils.nowdate()
    result = frappe.db.sql(
        """
        SELECT 
            AVG(CASE 
                WHEN creation >= %(from_date)s AND creation <= %(to_date)s  AND feedback_rating != ''
                THEN feedback_rating 
                ELSE NULL
            END) as current_month_avg,
            AVG(CASE 
                WHEN creation >= %(prev_from_date)s AND creation < %(from_date)s AND feedback_rating != ''
                THEN feedback_rating 
                ELSE NULL
            END) as prev_month_avg
        FROM `tabHD Ticket`
        WHERE 
            (creation >= %(prev_from_date)s AND creation <= %(to_date)s)
            AND feedback_rating IS NOT NULL
    """,
        {
            "from_date": from_date,
            "to_date": to_date,
            "prev_from_date": frappe.utils.add_months(from_date, -1),
        },
        as_dict=1,
    )

    current_month_avg = result[0].current_month_avg or 0
    prev_month_avg = result[0].prev_month_avg or 0

    delta = current_month_avg - prev_month_avg
    print("\n\n", result, "\n\n")

    return {
        "title": "Avg. Feedback Rating",
        "value": current_month_avg * 5,
        "suffix": "/5",
        "delta": delta * 5,
        "deltaSuffix": " stars",
    }


def get_master_dashboard_data(from_date, to_date):
    doctypes = ["HD Team", "HD Ticket Type", "HD Ticket Priority"]

    from_date = frappe.utils.add_days(frappe.utils.nowdate(), -30)
    to_date = frappe.utils.nowdate()

    team_data = get_team_chart_data(from_date, to_date)
    ticket_type_data = get_ticket_type_chart_data(from_date, to_date)
    ticket_priority_data = get_ticket_priority_chart_data(from_date, to_date)
    ticket_channel_data = get_ticket_channel_chart_data(from_date, to_date)

    return [team_data, ticket_type_data, ticket_priority_data, ticket_channel_data]


def get_team_chart_data(from_date, to_date):
    """
    Get team chart data for the dashboard.
    """
    result = frappe.get_all(
        "HD Ticket",
        fields=["agent_group as team", "count(name) as count"],
        filters={
            "creation": ["between", [from_date, to_date]],
        },
        group_by="agent_group",
    )
    # based on length show different chart, if len greater than 5 then show pie chart else bar chart
    if len(result) < 5:
        return get_pie_chart_config(
            result,
            "Tickets by Team",
            "Percentage of Total Tickets by Team",
            "team",
            "count",
        )
    else:
        return get_bar_chart_config(result)


def get_ticket_type_chart_data(from_date, to_date):
    """
    Get ticket type chart data for the dashboard.
    """
    result = frappe.get_all(
        "HD Ticket",
        fields=["ticket_type as type", "count(name) as count"],
        filters={
            "creation": ["between", [from_date, to_date]],
        },
        group_by="ticket_type",
    )
    # based on length show different chart, if len greater than 5 then show pie chart else bar chart
    if len(result) < 5:
        return get_pie_chart_config(
            result,
            "Tickets by Type",
            "Percentage of Total Tickets by Type",
            "type",
            "count",
        )
    else:
        return get_bar_chart_config(result)


def get_ticket_priority_chart_data(from_date, to_date):
    """
    Get ticket priority chart data for the dashboard.
    """
    result = frappe.get_all(
        "HD Ticket",
        fields=["priority as priority", "count(name) as count"],
        filters={
            "creation": ["between", [from_date, to_date]],
        },
        group_by="priority",
    )
    # based on length show different chart, if len greater than 5 then show pie chart else bar chart
    if len(result) < 5:
        return get_pie_chart_config(
            result,
            "Tickets by Priority",
            "Percentage of Total Tickets by Priority",
            "priority",
            "count",
        )
    else:
        return get_bar_chart_config(result)


def get_ticket_channel_chart_data(from_date, to_date):
    """
    Get ticket channel chart data for the dashboard.
    """
    result = frappe.get_all(
        "HD Ticket",
        fields=["via_customer_portal as channel ", "count(name) as count"],
        filters={
            "creation": ["between", [from_date, to_date]],
        },
        group_by="via_customer_portal",
        order_by="via_customer_portal desc",
        debug=1,
    )

    for row in result:
        row.channel = "Portal" if row.channel == 1 else "Email"

    return get_pie_chart_config(
        result,
        "Tickets by Channel",
        "Percentage of Total Tickets by Channel",
        "channel",
        "count",
    )


def get_pie_chart_config(data, title, subtitle, categoryColumn, valueColumn):
    return {
        "type": "pie",
        "data": data,
        "title": title,
        "subtitle": subtitle,
        "categoryColumn": categoryColumn,
        "valueColumn": valueColumn,
    }


def get_bar_chart_config(data):
    pass
