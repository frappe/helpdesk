import frappe
from frappe import _

from helpdesk.utils import agent_only, is_version_16

HD_TICKET = "HD Ticket"

COUNT_NAME = (
    {"COUNT": "name", "as": "count"} if is_version_16() else "count(name) as count"
)

COUNT_DESC = "count desc"


@frappe.whitelist()
@agent_only
def get_dashboard_data(
    dashboard_type: str, filters: dict[str, any] = None
) -> list[dict[str, any]] | None:
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

    open_statuses = tuple(
        frappe.get_all(
            "HD Ticket Status",
            filters={"category": "Open"},
            pluck="name",
        )
    )
    resolved_statuses = tuple(
        frappe.get_all(
            "HD Ticket Status",
            filters={"category": "Resolved"},
            pluck="name",
        )
    )

    if dashboard_type == "number_card":
        return get_number_card_data(from_date, to_date, conds, resolved_statuses)
    elif dashboard_type == "master":
        return get_master_dashboard_data(
            from_date, to_date, _filters.team, _filters.agent
        )
    elif dashboard_type == "trend":
        return get_trend_data(
            from_date, to_date, conds, open_statuses, resolved_statuses
        )


def get_number_card_data(
    from_date: str,
    to_date: str,
    conds: str = "",
    resolved_statuses: tuple[str, ...] = None,
) -> list[dict[str, any]]:
    """
    Get number card data for the dashboard.
    """

    ticket_chart_data = get_ticket_count(from_date, to_date, conds)
    sla_fulfilled_count = get_sla_fulfilled_count(
        from_date, to_date, conds, resolved_statuses
    )
    avg_first_response_time = get_avg_first_response_time(from_date, to_date, conds)
    avg_resolution_time = get_avg_resolution_time(
        from_date, to_date, conds, resolved_statuses
    )
    avg_feedback_score = get_avg_feedback_score(from_date, to_date, conds)

    return [
        ticket_chart_data,
        sla_fulfilled_count,
        avg_first_response_time,
        avg_resolution_time,
        avg_feedback_score,
    ]


def get_ticket_count(
    from_date: str, to_date: str, conds: str = "", return_result: bool = False
) -> dict[str, any]:
    """
    Get ticket data for the dashboard.
    """
    diff = frappe.utils.date_diff(to_date, from_date)
    if diff == 0:
        diff = 1

    result = frappe.db.sql(
        f"""
		SELECT
            COUNT(CASE
                WHEN creation >= %(from_date)s AND creation < DATE_ADD(%(to_date)s, INTERVAL 1 DAY)
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
		FROM `tabHD Ticket` # noqa: W604
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
        "title": _("Tickets"),
        "value": current_month_tickets,
        "delta": delta_in_percentage,
        "deltaSuffix": "%",
        "negativeIsBetter": True,
        "tooltip": _("Total number of tickets created"),
    }


def get_sla_fulfilled_count(
    from_date: str,
    to_date: str,
    conds: str = "",
    resolved_statuses: tuple[str, ...] = None,
) -> dict[str, any]:
    """
    Get the percent of SLA tickets fulfilled for the dashboard.
    """
    diff = frappe.utils.date_diff(to_date, from_date)
    if diff == 0:
        diff = 1

    result = frappe.db.sql(
        f"""
        SELECT 
            COUNT(CASE 
                WHEN creation >= %(from_date)s AND creation < DATE_ADD(%(to_date)s, INTERVAL 1 DAY) AND agreement_status = 'Fulfilled'
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
        FROM `tabHD Ticket` # noqa: W604
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

    # Only these tickets should be counted
    conds += f" AND status in {resolved_statuses}"

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
        "title": _("% SLA Fulfilled"),
        "value": current_month_fulfilled_percentage,
        "suffix": "%",
        "delta": delta_in_percentage,
        "deltaSuffix": "%",
        "tooltip": _("% of tickets created that were resolved within SLA"),
    }


def get_avg_first_response_time(
    from_date: str, to_date: str, conds: str = ""
) -> dict[str, any]:
    """
    first_response_time is the time taken to first respond to a ticket.
    Get average first response time for the dashboard.
    """
    diff = frappe.utils.date_diff(to_date, from_date)
    if diff == 0:
        diff = 1

    result = frappe.db.sql(
        f"""
        SELECT 
            AVG(CASE 
                WHEN creation >= %(from_date)s AND creation < DATE_ADD(%(to_date)s, INTERVAL 1 DAY) AND first_responded_on IS NOT NULL
                {conds}
                THEN first_response_time / 3600
                ELSE NULL
            END) as current_month_avg,
            AVG(CASE 
                When creation >= %(prev_from_date)s AND creation < %(from_date)s AND first_responded_on IS NOT NULL
                {conds}
                THEN first_response_time / 3600
                ELSE NULL
            END) as prev_month_avg
        FROM `tabHD Ticket` # noqa: W604
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
    suffix = _("hrs")

    return {
        "title": _("Avg. First Response"),
        "value": current_month_avg,
        "suffix": " " + suffix,
        "delta": delta,
        "deltaSuffix": " " + suffix,
        "negativeIsBetter": True,
        "tooltip": _("Avg. time taken to first respond to a ticket"),
    }


def get_avg_resolution_time(
    from_date: str,
    to_date: str,
    conds: str = "",
    resolved_statuses: tuple[str, ...] = None,
) -> dict[str, any]:
    """
    Get average resolution time for the dashboard.
    """
    diff = frappe.utils.date_diff(to_date, from_date)
    if diff == 0:
        diff = 1

    result = frappe.db.sql(
        f"""
        SELECT 
            AVG(CASE 
                WHEN status in {resolved_statuses} AND creation >= %(from_date)s AND creation < DATE_ADD(%(to_date)s, INTERVAL 1 DAY)
                {conds}
                THEN CEIL(resolution_time / 86400)
                ELSE NULL
            END) as current_month_avg,
            AVG(CASE 
                When status in {resolved_statuses} AND creation >= %(prev_from_date)s AND creation < %(from_date)s
                {conds}
                THEN CEIL(resolution_time / 86400)
                ELSE NULL
            END) as prev_month_avg
        FROM `tabHD Ticket` # noqa: W604
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
    suffix = _("days")

    return {
        "title": _("Avg. Resolution"),
        "value": current_month_avg,
        "suffix": " " + suffix,
        "delta": delta,
        "deltaSuffix": " " + suffix,
        "negativeIsBetter": True,
        "tooltip": _("Avg. time taken to resolve a ticket"),
    }


def get_avg_feedback_score(from_date: str, to_date: str, conds: str = ""):
    """
    Get average feedback score for the dashboard.
    """
    diff = frappe.utils.date_diff(to_date, from_date)
    if diff == 0:
        diff = 1

    result = frappe.db.sql(
        f"""
        SELECT 
            AVG(CASE 
                WHEN creation >= %(from_date)s AND creation < DATE_ADD(%(to_date)s, INTERVAL 1 DAY) AND feedback_rating > 0
                {conds}
                THEN feedback_rating 
                ELSE NULL
            END) as current_month_avg,
            AVG(CASE 
                WHEN creation >= %(prev_from_date)s AND creation < %(from_date)s AND feedback_rating > 0 
                {conds}
                THEN feedback_rating 
                ELSE NULL
            END) as prev_month_avg
        FROM `tabHD Ticket` # noqa: W604
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
    suffix = _("stars")

    return {
        "title": _("Avg. Feedback Rating"),
        "value": current_month_avg * 5,
        "suffix": "/5",
        "delta": delta * 5,
        "deltaSuffix": " " + suffix,
        "tooltip": _("Avg. feedback rating for the tickets resolved"),
    }


def get_master_dashboard_data(
    from_date: str, to_date: str, team: str = None, agent: str = None
) -> list[dict[str, any]]:
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


def get_team_chart_data(
    from_date: str, to_date: str, filters: dict[str, any] = None
) -> dict[str, any]:
    """
    Get team chart data for the dashboard.
    """
    result = frappe.get_all(
        HD_TICKET,
        fields=["agent_group as team", COUNT_NAME],
        filters=filters,
        group_by="agent_group",
        order_by=COUNT_DESC,
    )
    for r in result:
        if not r.team:
            r.team = _("No Team")

    if len(result) < 7:
        return get_pie_chart_config(
            result,
            _("Tickets by Team"),
            _("Percentage of Total Tickets by Team"),
            "team",
            "count",
        )
    else:
        return get_bar_chart_config(
            result,
            _("Tickets by Team"),
            _("Total Tickets by Team"),
            {"key": "team", "type": "category", "title": "Team", "timeGrain": "day"},
            "Tickets",
            [{"name": "count", "type": "bar"}],
        )


def get_ticket_type_chart_data(
    from_date: str, to_date: str, filters: dict[str, any] = None
) -> dict[str, any]:
    """
    Get ticket type chart data for the dashboard.
    """
    result = frappe.get_all(
        HD_TICKET,
        fields=["ticket_type as type", COUNT_NAME],
        filters=filters,
        group_by="ticket_type",
        order_by=COUNT_DESC,
    )
    # based on length show different chart, if len greater than 5 then show pie chart else bar chart
    if len(result) < 7:
        return get_pie_chart_config(
            result,
            _("Tickets by Type"),
            _("Percentage of Total Tickets by Type"),
            "type",
            "count",
        )
    else:
        return get_bar_chart_config(
            result,
            _("Tickets by Type"),
            _("Total Tickets by Type"),
            {"key": "type", "type": "category", "title": "Type", "timeGrain": "day"},
            "Tickets",
            [{"name": "count", "type": "bar"}],
        )


def get_ticket_priority_chart_data(
    from_date: str, to_date: str, filters: dict[str, any] = None
) -> dict[str, any]:
    """
    Get ticket priority chart data for the dashboard.
    """
    result = frappe.get_all(
        HD_TICKET,
        fields=["priority as priority", COUNT_NAME],
        filters=filters,
        group_by="priority",
        order_by=COUNT_DESC,
    )
    # based on length show different chart, if len greater than 5 then show pie chart else bar chart
    if len(result) < 7:
        return get_pie_chart_config(
            result,
            _("Tickets by Priority"),
            _("Percentage of Total Tickets by Priority"),
            "priority",
            "count",
        )
    else:
        return get_bar_chart_config(
            result,
            _("Tickets by Priority"),
            _("Total Tickets by Priority"),
            {
                "key": "priority",
                "type": "category",
                "title": "Priority",
                "timeGrain": "day",
            },
            "Tickets",
            [{"name": "count", "type": "bar"}],
        )


def get_ticket_channel_chart_data(
    from_date: str, to_date: str, filters: dict[str, any] = None
) -> dict[str, any]:
    """
    Get ticket channel chart data for the dashboard.
    """
    result = frappe.get_all(
        HD_TICKET,
        fields=["via_customer_portal as channel ", COUNT_NAME],
        filters=filters,
        group_by="via_customer_portal",
        order_by="via_customer_portal desc",
    )

    for row in result:
        row.channel = "Portal" if row.channel == 1 else "Email"

    return get_pie_chart_config(
        result,
        _("Tickets by Channel"),
        _("Percentage of Total Tickets by Channel"),
        "channel",
        "count",
    )


def get_trend_data(
    from_date: str,
    to_date: str,
    conds: str = "",
    open_statuses: tuple[str, ...] = None,
    resolved_statuses: tuple[str, ...] = None,
) -> list[dict[str, any]]:
    """
    Get trend data for the dashboard.
    """

    ticket_trend_data = get_ticket_trend_data(
        from_date, to_date, conds, open_statuses, resolved_statuses
    )
    feedback_trend_data = get_feedback_trend_data(from_date, to_date, conds)

    return [
        ticket_trend_data,
        feedback_trend_data,
    ]


def get_ticket_trend_data(
    from_date: str,
    to_date: str,
    conds: str = "",
    open_statuses: tuple[str, ...] = None,
    resolved_statuses: tuple[str, ...] = None,
) -> dict[str, any]:
    """
    Trend data for tickets in the dashboard. Ticket trend +SLA fulfilled
    """
    if len(open_statuses) == 1:
        open_statuses = f"('{open_statuses[0]}')"

    open_status = _("open")
    closed_status = _("closed")
    sla_fulfilled_status = _("SLA_fulfilled")

    result = frappe.db.sql(
        f"""
            SELECT 
                DATE(creation) as date,
                COUNT(CASE WHEN status in {open_statuses} THEN name END) as {open_status},
                COUNT(CASE WHEN status in {resolved_statuses} THEN name END) as {closed_status},
                COUNT(CASE WHEN agreement_status = 'Fulfilled' THEN name END) as {sla_fulfilled_status}
            FROM `tabHD Ticket` # noqa: W604
            WHERE creation > %(from_date)s AND creation < DATE_ADD(%(to_date)s, INTERVAL 1 DAY)
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
    subtitle = _("Average tickets per day is around {0}").format(
        "{:.0f}".format(avg_tickets)
    )
    return get_bar_chart_config(
        result,
        _("Ticket Trend"),
        subtitle,
        {"key": "date", "type": "time", "title": "Date", "timeGrain": "day"},
        _("Tickets"),
        [
            {"name": closed_status, "type": "bar"},
            {"name": open_status, "type": "bar"},
            {
                "name": _("SLA_fulfilled"),
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


def get_feedback_trend_data(
    from_date: str, to_date: str, conds: str = ""
) -> dict[str, any]:
    """
    Get feedback trend data for the dashboard.
    """

    rating = _("rating")
    rated_tickets = _("rated_tickets")

    result = frappe.db.sql(
        f"""
        SELECT 
            DATE(creation) as date,
            AVG(CASE WHEN feedback_rating > 0 THEN feedback_rating END) * 5 as {rating},
            COUNT(CASE WHEN feedback_rating > 0 THEN name END) as {rated_tickets}
        FROM `tabHD Ticket` # noqa: W604
        WHERE 
            creation > %(from_date)s AND creation < DATE_ADD(%(to_date)s, INTERVAL 1 DAY)
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
        FROM `tabHD Ticket` # noqa: W604
        WHERE 
            creation BETWEEN %(from_date)s AND DATE_ADD(%(to_date)s, INTERVAL 1 DAY)
            {conds}
            AND feedback_rating > 0
    """,
        {
            "from_date": from_date,
            "to_date": to_date,
        },
        pluck=True,
    )
    avg_rating = avg_rating_result[0] if avg_rating_result[0] else 0

    subtitle = _("Average feedback rating per day is around {0} stars").format(
        "{:.1f}".format(avg_rating)
    )

    return get_bar_chart_config(
        result,
        _("Feedback Trend"),
        subtitle,
        {"key": "date", "type": "time", "title": "Date", "timeGrain": "day"},
        _("Rated Tickets"),
        [
            {"name": rated_tickets, "type": "bar"},
            {
                "name": rating,
                "type": "line",
                "showDataPoints": True,
                "axis": "y2",
                "color": "#48BB74",
            },
        ],
        y2Axis={
            "title": _("Rating"),
            "yMin": 0,
            "yMax": 5,
        },
    )


def get_pie_chart_config(
    data: list[dict[str, any]],
    title: str,
    subtitle: str,
    category_column: str,
    value_column: str,
) -> dict[str, any]:
    return {
        "type": "pie",
        "data": data,
        "title": title,
        "subtitle": subtitle,
        "categoryColumn": category_column,
        "valueColumn": value_column,
    }


def get_bar_chart_config(
    data: list[dict[str, any]],
    title: str,
    subtitle: str,
    x_axis_config: dict[str, any],
    y_axis_title: str,
    series: list,
    **kwargs: dict[str, any],
) -> dict[str, any]:
    return {
        "type": "axis",
        "data": data,
        "title": title,
        "subtitle": subtitle,
        "xAxis": x_axis_config,
        "yAxis": {"title": y_axis_title},
        "series": series,
        **kwargs,
    }


def get_conditions_from_filters(filters: dict[str, any]) -> str:
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


def get_avg_tickets_per_day(from_date: str, to_date: str, conds: str = "") -> float:
    """
    Get average tickets per day for the dashboard.
    """
    result = frappe.db.sql(
        f"""
            SELECT 
                COUNT(name) as total_tickets,
                DATEDIFF(DATE_ADD(%(to_date)s, INTERVAL 1 DAY), %(from_date)s) as days
            FROM `tabHD Ticket` # noqa: W604
            WHERE creation > %(from_date)s AND creation < DATE_ADD(%(to_date)s, INTERVAL 1 DAY)
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
    return avg_tickets_per_day
