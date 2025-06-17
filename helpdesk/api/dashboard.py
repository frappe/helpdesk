import frappe
from frappe import _

from helpdesk.utils import agent_only


@frappe.whitelist()
@agent_only
def get_dashboard_data(dashboard_type, filters=None):
    """
    Get dashboard data based on the type and date range.
    """
    user = frappe.session.user
    is_manager = "Agent Manager" in frappe.get_roles(user)

    if not is_manager and (filters.get("agent") != user or filters.get("team")):
        frappe.throw(
            _("You are not allowed to view this dashboard data."),
            frappe.PermissionError,
        )
        return

    from_date = filters.get("from_date") if filters else None
    to_date = filters.get("to_date") if filters else None
    team = filters.get("team") if filters else None
    agent = filters.get("agent") if filters else None

    if agent == "@me":
        agent = frappe.session.user

    if not from_date:
        from_date = frappe.utils.add_days(frappe.utils.nowdate(), -30)
    if not to_date:
        to_date = frappe.utils.nowdate()

    _filters = frappe._dict(
        from_date=from_date,
        to_date=to_date,
        team=team,
        agent=agent,
    )
    conds = ""
    if _filters.team:
        conds += f" AND agent_group='{_filters.team}'"

    if _filters.agent:
        conds += f" AND JSON_SEARCH(_assign, 'one', '{_filters.agent}') IS NOT NULL"

    if dashboard_type == "number_card":
        return get_number_card_data(from_date, to_date, conds)
    elif dashboard_type == "master":
        return get_master_dashboard_data(
            from_date, to_date, _filters.team, _filters.agent
        )
    elif dashboard_type == "trend":
        return get_trend_data(from_date, to_date, conds)


def get_number_card_data(from_date, to_date, conds=""):
    """
    Get number card data for the dashboard.
    """

    ticket_chart_data = get_ticket_count(from_date, to_date, conds)
    resolved_tickets = get_resolved_tickets(from_date, to_date, conds)
    sla_fulfilled_count = get_sla_fulfilled_count(from_date, to_date, conds)
    avg_resolution_time = get_avg_resolution_time(from_date, to_date, conds)
    avg_feedback_score = get_avg_feedback_score(from_date, to_date, conds)

    return [
        ticket_chart_data,
        resolved_tickets,
        sla_fulfilled_count,
        avg_resolution_time,
        avg_feedback_score,
    ]


def get_ticket_count(from_date, to_date, conds="", return_result=False):
    """
    Get ticket data for the dashboard.
    """
    diff = frappe.utils.date_diff(to_date, from_date)

    result = frappe.db.sql(
        f"""
		SELECT
				COUNT(CASE
					WHEN creation >= %(from_date)s AND creation <= %(to_date)s 
                    {conds}
					THEN name
					ELSE NULL
				END) as current_month_tickets,

				COUNT(CASE
					WHEN creation >= %(prev_from_date)s AND creation < %(from_date)s 
                    {conds}
					THEN name
					ELSE NULL
				END) as prev_month_tickets
		FROM `tabHD Ticket`
    """,
        {
            "from_date": from_date,
            "to_date": to_date,
            "prev_from_date": frappe.utils.add_days(from_date, -diff),
        },
        as_dict=1,
    )

    if return_result:
        return result

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


def get_resolved_tickets(from_date, to_date, conds=""):
    """
    Get resolved tickets for the dashboard.
    Get the ticket count for the current month also get tickets resolved or closed in the current month
    same for the previous month.
    """
    diff = frappe.utils.date_diff(to_date, from_date)

    result = frappe.db.sql(
        f"""
        SELECT 
            COUNT(CASE 
                WHEN creation >= %(from_date)s AND creation <= %(to_date)s AND status IN ('Resolved', 'Closed')
                {conds}
                THEN name 
                ELSE NULL
            END) as current_month_resolved,
            COUNT(CASE 
                WHEN creation >= %(prev_from_date)s AND creation < %(from_date)s AND status IN ('Resolved', 'Closed')
                {conds}
                THEN name 
                ELSE NULL
            END) as prev_month_resolved
        FROM `tabHD Ticket`
    """,
        {
            "from_date": from_date,
            "to_date": to_date,
            "prev_from_date": frappe.utils.add_days(from_date, -diff),
        },
        as_dict=1,
    )

    current_month_resolved = result[0].current_month_resolved or 0
    prev_month_resolved = result[0].prev_month_resolved or 0
    ticket_count = (
        get_ticket_count(from_date, to_date, conds, True)[0] if len(result) > 0 else 1
    )

    current_month_resolved_percentage = (
        current_month_resolved / ticket_count.current_month_tickets * 100
        if ticket_count.current_month_tickets
        else 0
    )
    prev_month_resolved_percentage = (
        prev_month_resolved / ticket_count.prev_month_tickets * 100
        if ticket_count.prev_month_tickets
        else 0
    )

    delta_in_percentage = (
        current_month_resolved_percentage - prev_month_resolved_percentage
    )
    return {
        "title": "% Resolved",
        "value": current_month_resolved_percentage,
        "suffix": "%",
        "delta": delta_in_percentage,
        "deltaSuffix": "%",
    }


def get_sla_fulfilled_count(from_date, to_date, conds=""):
    """
    Get the percent of SLA tickets fulfilled for the dashboard.
    """
    diff = frappe.utils.date_diff(to_date, from_date)

    result = frappe.db.sql(
        f"""
        SELECT 
            COUNT(CASE 
                WHEN creation >= %(from_date)s AND creation <= %(to_date)s AND agreement_status = 'Fulfilled'
                {conds}
                THEN name 
                ELSE NULL
            END) as current_month_fulfilled,
            COUNT(CASE 
                WHEN creation >= %(prev_from_date)s AND creation < %(from_date)s AND agreement_status = 'Fulfilled'
                {conds}
                THEN name 
                ELSE NULL
            END) as prev_month_fulfilled
        FROM `tabHD Ticket`
    """,
        {
            "from_date": from_date,
            "to_date": to_date,
            "prev_from_date": frappe.utils.add_days(from_date, -diff),
        },
        as_dict=1,
    )

    current_month_fulfilled = result[0].current_month_fulfilled or 0
    prev_month_fulfilled = result[0].prev_month_fulfilled or 0
    ticket_count = (
        get_ticket_count(from_date, to_date, conds, True)[0] if len(result) > 0 else 1
    )

    current_month_fulfilled_percentage = (
        current_month_fulfilled / ticket_count.current_month_tickets * 100
        if ticket_count.current_month_tickets
        else 0
    )
    prev_month_fulfilled_percentage = (
        prev_month_fulfilled / ticket_count.prev_month_tickets * 100
        if ticket_count.prev_month_tickets
        else 0
    )
    delta_in_percentage = (
        current_month_fulfilled_percentage - prev_month_fulfilled_percentage
    )
    return {
        "title": "% SLA Fulfilled",
        "value": current_month_fulfilled_percentage,
        "suffix": "%",
        "delta": delta_in_percentage,
        "deltaSuffix": "%",
    }


def get_avg_resolution_time(from_date, to_date, conds=""):
    """
    Get average resolution time for the dashboard.
    """
    diff = frappe.utils.date_diff(to_date, from_date)

    result = frappe.db.sql(
        f"""
        SELECT 
            AVG(CASE 
                WHEN status in ('Resolved', 'Closed') AND creation >= %(from_date)s AND creation <= %(to_date)s
                {conds}
                THEN TIMESTAMPDIFF(DAY, creation, resolution_date)
                ELSE NULL
            END) as current_month_avg,
            AVG(CASE 
                When status in ('Resolved', 'Closed') AND creation >= %(prev_from_date)s AND creation < %(from_date)s
                {conds}
                THEN TIMESTAMPDIFF(DAY, creation, resolution_date)
                ELSE NULL
            END) as prev_month_avg
        FROM `tabHD Ticket`
    """,
        {
            "from_date": from_date,
            "to_date": to_date,
            "prev_from_date": frappe.utils.add_days(from_date, -diff),
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


def get_avg_feedback_score(from_date, to_date, conds=""):
    """
    Get average feedback score for the dashboard.
    """
    diff = frappe.utils.date_diff(to_date, from_date)
    result = frappe.db.sql(
        f"""
        SELECT 
            AVG(CASE 
                WHEN creation >= %(from_date)s AND creation <= %(to_date)s  AND feedback_rating != ''
                {conds}
                THEN feedback_rating 
                ELSE NULL
            END) as current_month_avg,
            AVG(CASE 
                WHEN creation >= %(prev_from_date)s AND creation < %(from_date)s AND feedback_rating != ''
                {conds}
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
            "prev_from_date": frappe.utils.add_days(from_date, -diff),
        },
        as_dict=1,
    )

    current_month_avg = result[0].current_month_avg or 0
    prev_month_avg = result[0].prev_month_avg or 0

    delta = current_month_avg - prev_month_avg

    return {
        "title": "Avg. Feedback Rating",
        "value": current_month_avg * 5,
        "suffix": "/5",
        "delta": delta * 5,
        "deltaSuffix": " stars",
    }


def get_master_dashboard_data(from_date, to_date, team=None, agent=None):
    filters = {
        "creation": ["between", [from_date, to_date]],
    }
    if team:
        filters["agent_group"] = team
    if agent:
        filters["_assign"] = ["like", f"%{agent}%"]
    team_data = get_team_chart_data(from_date, to_date, filters)
    ticket_type_data = get_ticket_type_chart_data(from_date, to_date, filters)
    ticket_priority_data = get_ticket_priority_chart_data(from_date, to_date, filters)
    ticket_channel_data = get_ticket_channel_chart_data(from_date, to_date, filters)

    return [team_data, ticket_type_data, ticket_priority_data, ticket_channel_data]


def get_team_chart_data(from_date, to_date, filters=None):
    """
    Get team chart data for the dashboard.
    """
    result = frappe.get_all(
        "HD Ticket",
        fields=["agent_group as team", "count(name) as count"],
        filters=filters,
        group_by="agent_group",
    )
    for r in result:
        if not r.team:
            r.team = "No Team"

    if len(result) < 7:
        return get_pie_chart_config(
            result,
            "Tickets by Team",
            "Percentage of Total Tickets by Team",
            "team",
            "count",
        )
    else:
        return get_bar_chart_config(
            result,
            "Tickets by Team",
            "Total Tickets by Team",
            {"key": "team", "type": "category", "title": "Team", "timeGrain": "day"},
            "Tickets",
            [{"name": "count", "type": "bar"}],
        )


def get_ticket_type_chart_data(from_date, to_date, filters=None):
    """
    Get ticket type chart data for the dashboard.
    """
    result = frappe.get_all(
        "HD Ticket",
        fields=["ticket_type as type", "count(name) as count"],
        filters=filters,
        group_by="ticket_type",
    )
    # based on length show different chart, if len greater than 5 then show pie chart else bar chart
    if len(result) < 7:
        return get_pie_chart_config(
            result,
            "Tickets by Type",
            "Percentage of Total Tickets by Type",
            "type",
            "count",
        )
    else:
        return get_bar_chart_config(
            result,
            "Tickets by Type",
            "Total Tickets by Type",
            {"key": "type", "type": "category", "title": "Type", "timeGrain": "day"},
            "Tickets",
            [{"name": "count", "type": "bar"}],
        )


def get_ticket_priority_chart_data(from_date, to_date, filters=None):
    """
    Get ticket priority chart data for the dashboard.
    """
    result = frappe.get_all(
        "HD Ticket",
        fields=["priority as priority", "count(name) as count"],
        filters=filters,
        group_by="priority",
    )
    # based on length show different chart, if len greater than 5 then show pie chart else bar chart
    if len(result) < 7:
        return get_pie_chart_config(
            result,
            "Tickets by Priority",
            "Percentage of Total Tickets by Priority",
            "priority",
            "count",
        )
    else:
        return get_bar_chart_config(
            result,
            "Tickets by Priority",
            "Total Tickets by Priority",
            {
                "key": "priority",
                "type": "category",
                "title": "Priority",
                "timeGrain": "day",
            },
            "Tickets",
            [{"name": "count", "type": "bar"}],
        )


def get_ticket_channel_chart_data(from_date, to_date, filters=None):
    """
    Get ticket channel chart data for the dashboard.
    """
    result = frappe.get_all(
        "HD Ticket",
        fields=["via_customer_portal as channel ", "count(name) as count"],
        filters=filters,
        group_by="via_customer_portal",
        order_by="via_customer_portal desc",
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


def get_trend_data(from_date, to_date, conds=""):
    """
    Get trend data for the dashboard.
    """

    ticket_trend_data = get_ticket_trend_data(from_date, to_date, conds)
    feedback_trend_data = get_feedback_trend_data(from_date, to_date, conds)

    return [
        ticket_trend_data,
        feedback_trend_data,
    ]


def get_ticket_trend_data(from_date, to_date, conds=""):
    """
    Trend data for tickets in the dashboard. Ticket treand +SLA fulfilled
    """
    result = frappe.db.sql(
        f"""
        SELECT 
            DATE(creation) as date,
            COUNT(CASE WHEN status = 'Open' THEN name END) as open,
            COUNT(CASE WHEN status IN ('Resolved', 'Closed') THEN name END) as closed,
            COUNT(CASE WHEN agreement_status = 'Fulfilled' THEN name END) as sla_fulfilled
        FROM `tabHD Ticket`
        WHERE creation BETWEEN %(from_date)s AND %(to_date)s
        {conds}
        GROUP BY DATE(creation)
        ORDER BY DATE(creation)
    """,
        {
            "from_date": from_date,
            "to_date": to_date,
        },
        as_dict=1,
    )
    avg_tickets = get_avg_tickets_per_day(from_date, to_date, conds)
    subtitle = f"Average tickets per day is around {avg_tickets:.0f}"
    return get_bar_chart_config(
        result,
        "Ticket Trend",
        subtitle,
        {"key": "date", "type": "time", "title": "Date", "timeGrain": "day"},
        "Tickets",
        [
            {"name": "closed", "type": "bar"},
            {"name": "open", "type": "bar"},
            {
                "name": "sla_fulfilled",
                "type": "line",
                "showDataPoints": True,
                "axis": "y2",
            },
        ],
        stacked=True,
        y2Axis={
            "title": "% SLA",
            "yMin": 0,
            "yMax": 100,
        },
    )


def get_feedback_trend_data(from_date, to_date, conds=""):
    """
    Get feedback trend data for the dashboard.
    """
    result = frappe.db.sql(
        f"""
        SELECT 
            DATE(creation) as date,
            AVG(CASE WHEN feedback_rating IS NOT NULL THEN feedback_rating END) * 5 as rating,
            COUNT(CASE WHEN feedback_rating IS NOT NULL THEN name END) as rated_tickets
        FROM `tabHD Ticket`
        WHERE 
            creation BETWEEN %(from_date)s AND %(to_date)s
            {conds}
        GROUP BY DATE(creation)
        ORDER BY DATE(creation)
    """,
        {
            "from_date": from_date,
            "to_date": to_date,
        },
        as_dict=1,
    )

    avg_rating_result = frappe.db.sql(
        f"""
        SELECT 
            AVG(feedback_rating) * 5 as avg_rating
        FROM `tabHD Ticket`
        WHERE 
            creation BETWEEN %(from_date)s AND %(to_date)s
            {conds}
    """,
        {
            "from_date": from_date,
            "to_date": to_date,
        },
        pluck=True,
    )
    avg_rating = avg_rating_result[0] if avg_rating_result[0] else 0

    subtitle = f"Average feedback rating per day is around {avg_rating:.1f} stars"

    return get_bar_chart_config(
        result,
        "Feedback Trend",
        subtitle,
        {"key": "date", "type": "time", "title": "Date", "timeGrain": "day"},
        "Rated Tickets",
        [
            {"name": "rated_tickets", "type": "bar"},
            {
                "name": "rating",
                "type": "line",
                "showDataPoints": True,
                "axis": "y2",
                "color": "#48BB74",
            },
        ],
        y2Axis={
            "title": "Rating",
            "yMin": 0,
            "yMax": 5,
        },
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


def get_bar_chart_config(
    data, title, subtitle, xAxisConfig, yAxisTitle, series, **kwargs
):
    return {
        "type": "axis",
        "data": data,
        "title": title,
        "subtitle": subtitle,
        "xAxis": xAxisConfig,
        "yAxis": {"title": yAxisTitle},
        "series": series,
        **kwargs,
    }


def get_conditions_from_filters(filters):
    """
    Get conditions from filters.
    """
    conditions = [
        f" AND creation between '{filters['from_date']}' and '{filters['to_date']}'"
    ]

    if filters.get("team"):
        conditions.append(f"agent_group = '{filters['team']}'")
    if filters.get("agent"):
        conditions.append(f"owner = '{filters['agent']}'")

    return " AND ".join(conditions) if conditions else ""


def get_avg_tickets_per_day(from_date, to_date, conds=""):
    """
    Get average tickets per day for the dashboard.
    """
    result = frappe.db.sql(
        f"""
        SELECT 
            COUNT(name) as total_tickets,
            DATEDIFF(%(to_date)s, %(from_date)s) as days
        FROM `tabHD Ticket`
        WHERE creation BETWEEN %(from_date)s AND %(to_date)s
        {conds}
    """,
        {
            "from_date": from_date,
            "to_date": to_date,
        },
        as_dict=1,
    )

    total_tickets = result[0].total_tickets or 0
    days = result[0].days or 1  # Avoid division by zero

    avg_tickets_per_day = total_tickets / days

    return avg_tickets_per_day
