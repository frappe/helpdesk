import operator
from functools import reduce

import frappe
from frappe import _
from frappe.query_builder import DocType
from frappe.query_builder.functions import Avg, Count, Function
from pypika import Case

from helpdesk.utils import agent_only, is_version_16

HD_TICKET = "HD Ticket"

COUNT_NAME = (
    {"COUNT": "name", "as": "count"} if is_version_16() else "count(name) as count"
)

COUNT_DESC = "count desc"


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

    dashboard = HelpdeskDashboard(_filters)

    if dashboard_type == "number_card":
        return dashboard.get_number_card_data()
    elif dashboard_type == "master":
        return get_master_dashboard_data(
            from_date, to_date, _filters.team, _filters.agent
        )
    elif dashboard_type == "trend":
        return dashboard.get_trend_data()


class HelpdeskDashboard:
    def __init__(self, filters):
        self.filters = filters
        self.from_date = filters.get("from_date")
        self.to_date = filters.get("to_date")
        self.team = filters.get("team")
        self.agent = filters.get("agent")

        self.ticket = DocType("HD Ticket")
        self.qb_conds = self._get_conditions()
        self.combined_cond = (
            reduce(operator.and_, self.qb_conds) if self.qb_conds else None
        )

        self.diff = frappe.utils.date_diff(self.to_date, self.from_date)
        if self.diff == 0:
            self.diff = 1
        self.prev_from_date = frappe.utils.add_days(self.from_date, -self.diff)
        self.to_date_next = frappe.utils.add_days(self.to_date, 1)

<<<<<<< HEAD
def get_number_card_data(from_date, to_date, conds="", resolved_statuses=None):
    """
    Get number card data for the dashboard.
    """
=======
        self.open_statuses = frappe.get_all(
            "HD Ticket Status",
            filters={"category": "Open"},
            pluck="name",
        )
        self.resolved_statuses = frappe.get_all(
            "HD Ticket Status",
            filters={"category": "Resolved"},
            pluck="name",
        )
>>>>>>> 1e1cd602 (refactor: convert dashboard api to class and add QB support)

    def _get_conditions(self):
        conds = []
        if self.team:
            conds.append(self.ticket.agent_group == self.team)
        if self.agent:
            # Pass args to Function(...) directly. ParameterizedFunction is not callable.
            conds.append(
                Function(
                    "JSON_SEARCH", self.ticket._assign, "one", self.agent
                ).isnotnull()
            )
        return conds

    def _get_case(self, start, end, value, func, extra_cond=None):
        cond = (self.ticket.creation >= start) & (self.ticket.creation < end)
        if extra_cond:
            cond = cond & extra_cond
        if self.combined_cond:
            cond = cond & self.combined_cond

        return func(Case().when(cond, value).else_(None))

<<<<<<< HEAD
def get_ticket_count(from_date, to_date, conds="", return_result=False):
    """
    Get ticket data for the dashboard.
    """
    diff = frappe.utils.date_diff(to_date, from_date)
    if diff == 0:
        diff = 1
=======
    def get_metric_data(self, value, func, extra_cond=None):
        current_expr = self._get_case(
            self.from_date, self.to_date_next, value, func, extra_cond
        )
        prev_expr = self._get_case(
            self.prev_from_date, self.from_date, value, func, extra_cond
        )
>>>>>>> 1e1cd602 (refactor: convert dashboard api to class and add QB support)

        query = frappe.qb.from_(self.ticket).select(
            current_expr.as_("current"), prev_expr.as_("prev")
        )
        result = query.run(as_dict=True)
        return result[0].current or 0, result[0].prev or 0

    def get_number_card_data(self):
        return [
            self.get_ticket_count(),
            self.get_sla_fulfilled_count(),
            self.get_avg_first_response_time(),
            self.get_avg_resolution_time(),
            self.get_avg_feedback_score(),
        ]

    def get_ticket_count(self):
        current, prev = self.get_metric_data(self.ticket.name, Count)
        delta = ((current - prev) / prev * 100) if prev else 0

        return {
            "title": _("Tickets"),
            "value": current,
            "delta": delta,
            "deltaSuffix": "%",
            "negativeIsBetter": True,
            "tooltip": _("Total number of tickets created"),
        }

    def get_sla_fulfilled_count(self):
        extra_cond = self.ticket.agreement_status == "Fulfilled"
        current_fulfilled, prev_fulfilled = self.get_metric_data(
            self.ticket.name, Count, extra_cond
        )

<<<<<<< HEAD
    return {
        "title": "Tickets",
        "value": current_month_tickets,
        "delta": delta_in_percentage,
        "deltaSuffix": "%",
        "negativeIsBetter": True,
        "tooltip": "Total number of tickets created",
    }
=======
        status_cond = (
            self.ticket.status.isin(self.resolved_statuses)
            if self.resolved_statuses
            else None
        )
        current_total, prev_total = self.get_metric_data(
            self.ticket.name, Count, status_cond
        )
>>>>>>> 1e1cd602 (refactor: convert dashboard api to class and add QB support)

        current_pct = (current_fulfilled / current_total * 100) if current_total else 0
        prev_pct = (prev_fulfilled / prev_total * 100) if prev_total else 0

<<<<<<< HEAD
def get_sla_fulfilled_count(from_date, to_date, conds="", resolved_statuses=None):
    """
    Get the percent of SLA tickets fulfilled for the dashboard.
    """
    diff = frappe.utils.date_diff(to_date, from_date)
    if diff == 0:
        diff = 1
=======
        return {
            "title": _("% SLA Fulfilled"),
            "value": current_pct,
            "suffix": "%",
            "delta": current_pct - prev_pct,
            "deltaSuffix": "%",
            "tooltip": _("% of tickets created that were resolved within SLA"),
        }
>>>>>>> 1e1cd602 (refactor: convert dashboard api to class and add QB support)

    def get_avg_first_response_time(self):
        extra_cond = self.ticket.first_responded_on.isnotnull()
        current, prev = self.get_metric_data(
            self.ticket.first_response_time / 3600, Avg, extra_cond
        )

        return {
            "title": _("Avg. First Response"),
            "value": current,
            "suffix": " " + _("hrs"),
            "delta": current - prev,
            "deltaSuffix": " " + _("hrs"),
            "negativeIsBetter": True,
            "tooltip": _("Avg. time taken to first respond to a ticket"),
        }

    def get_avg_resolution_time(self):
        extra_cond = (
            self.ticket.status.isin(self.resolved_statuses)
            if self.resolved_statuses
            else None
        )
        value_expr = Function("CEIL", self.ticket.resolution_time / 86400)
        current, prev = self.get_metric_data(value_expr, Avg, extra_cond)

        return {
            "title": _("Avg. Resolution"),
            "value": current,
            "suffix": " " + _("days"),
            "delta": current - prev,
            "deltaSuffix": " " + _("days"),
            "negativeIsBetter": True,
            "tooltip": _("Avg. time taken to resolve a ticket"),
        }

<<<<<<< HEAD
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
        "tooltip": "% of tickets created that were resolved within SLA",
    }
=======
    def get_avg_feedback_score(self):
        extra_cond = self.ticket.feedback_rating > 0
        current, prev = self.get_metric_data(
            self.ticket.feedback_rating, Avg, extra_cond
        )
>>>>>>> 1e1cd602 (refactor: convert dashboard api to class and add QB support)

        return {
            "title": _("Avg. Feedback Rating"),
            "value": current * 5,
            "suffix": "/5",
            "delta": (current - prev) * 5,
            "deltaSuffix": " " + _("stars"),
            "tooltip": _("Avg. feedback rating for the tickets resolved"),
        }

<<<<<<< HEAD
def get_avg_first_response_time(from_date, to_date, conds=""):
    """
    first_response_time is the time taken to first respond to a ticket.
    Get average first response time for the dashboard.
    """
    diff = frappe.utils.date_diff(to_date, from_date)
    if diff == 0:
        diff = 1
=======
    def get_trend_data(self):
        return [
            self.get_ticket_trend_data(),
            self.get_feedback_trend_data(),
        ]
>>>>>>> 1e1cd602 (refactor: convert dashboard api to class and add QB support)

    def get_ticket_trend_data(self):
        open_status = "Open"
        closed_status = "Closed"
        sla_fulfilled_status = "SLA Fulfilled"

        base_cond = (self.ticket.creation > self.from_date) & (
            self.ticket.creation < self.to_date_next
        )
        if self.combined_cond:
            base_cond = base_cond & self.combined_cond

<<<<<<< HEAD
    delta = current_month_avg - prev_month_avg if prev_month_avg else 0

    return {
        "title": "Avg. First Response",
        "value": current_month_avg,
        "suffix": " hrs",
        "delta": delta,
        "deltaSuffix": " hrs",
        "negativeIsBetter": True,
        "tooltip": "Avg. time taken to first respond to a ticket",
    }
=======
        query = (
            frappe.qb.from_(self.ticket)
            .select(
                Function("DATE", self.ticket.creation).as_("date"),
                Count(
                    Case()
                    .when(self.ticket.status.isin(self.open_statuses), self.ticket.name)
                    .else_(None)
                ).as_(open_status),
                Count(
                    Case()
                    .when(
                        self.ticket.status.isin(self.resolved_statuses),
                        self.ticket.name,
                    )
                    .else_(None)
                ).as_(closed_status),
                Count(
                    Case()
                    .when(self.ticket.agreement_status == "Fulfilled", self.ticket.name)
                    .else_(None)
                ).as_(sla_fulfilled_status),
            )
            .where(base_cond)
            .groupby(Function("DATE", self.ticket.creation))
            .orderby(Function("DATE", self.ticket.creation))
        )

        result = query.run(as_dict=True)
        avg_tickets = self.get_avg_tickets_per_day()
        subtitle = _("Average tickets per day is around {0}").format(
            "{:.0f}".format(avg_tickets)
        )
>>>>>>> 1e1cd602 (refactor: convert dashboard api to class and add QB support)

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
                    "name": sla_fulfilled_status,
                    "type": "line",
                    "showDataPoints": True,
                    "axis": "y2",
                },
            ],
            stacked=True,
            y2Axis={"title": "% SLA", "yMin": 0, "yMax": 100},
        )

<<<<<<< HEAD
def get_avg_resolution_time(from_date, to_date, conds="", resolved_statuses=None):
    """
    Get average resolution time for the dashboard.
    """
    diff = frappe.utils.date_diff(to_date, from_date)
    if diff == 0:
        diff = 1
=======
    def get_feedback_trend_data(self):
        rating = "Rating"
        rated_tickets = "Rated Tickets"
>>>>>>> 1e1cd602 (refactor: convert dashboard api to class and add QB support)

        base_cond = (self.ticket.creation > self.from_date) & (
            self.ticket.creation < self.to_date_next
        )
        if self.combined_cond:
            base_cond = base_cond & self.combined_cond

<<<<<<< HEAD
    delta = current_month_avg - prev_month_avg if prev_month_avg else 0
    return {
        "title": "Avg. Resolution",
        "value": current_month_avg,
        "suffix": " days",
        "delta": delta,
        "deltaSuffix": " days",
        "negativeIsBetter": True,
        "tooltip": "Avg. time taken to resolve a ticket",
    }
=======
        query = (
            frappe.qb.from_(self.ticket)
            .select(
                Function("DATE", self.ticket.creation).as_("date"),
                (
                    Avg(
                        Case()
                        .when(
                            self.ticket.feedback_rating > 0, self.ticket.feedback_rating
                        )
                        .else_(None)
                    )
                    * 5
                ).as_(rating),
                Count(
                    Case()
                    .when(self.ticket.feedback_rating > 0, self.ticket.name)
                    .else_(None)
                ).as_(rated_tickets),
            )
            .where(base_cond)
            .groupby(Function("DATE", self.ticket.creation))
            .orderby(Function("DATE", self.ticket.creation))
        )

        result = query.run(as_dict=True)
>>>>>>> 1e1cd602 (refactor: convert dashboard api to class and add QB support)

        # Avg rating query
        avg_query = (
            frappe.qb.from_(self.ticket)
            .select((Avg(self.ticket.feedback_rating) * 5).as_("avg_rating"))
            .where(
                (self.ticket.creation.between(self.from_date, self.to_date_next))
                & (self.ticket.feedback_rating > 0)
            )
        )
        if self.combined_cond:
            avg_query = avg_query.where(self.combined_cond)

<<<<<<< HEAD
def get_avg_feedback_score(from_date, to_date, conds=""):
    """
    Get average feedback score for the dashboard.
    """
    diff = frappe.utils.date_diff(to_date, from_date)
    if diff == 0:
        diff = 1
=======
        avg_rating_result = avg_query.run(pluck=True)
        avg_rating = (
            avg_rating_result[0] if avg_rating_result and avg_rating_result[0] else 0
        )
>>>>>>> 1e1cd602 (refactor: convert dashboard api to class and add QB support)

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
            y2Axis={"title": _("Rating"), "yMin": 0, "yMax": 5},
        )

<<<<<<< HEAD
    delta = current_month_avg - prev_month_avg

    return {
        "title": "Avg. Feedback Rating",
        "value": current_month_avg * 5,
        "suffix": "/5",
        "delta": delta * 5,
        "deltaSuffix": " stars",
        "tooltip": "Avg. feedback rating for the tickets resolved",
    }
=======
    def get_avg_tickets_per_day(self):
        base_cond = (self.ticket.creation > self.from_date) & (
            self.ticket.creation < self.to_date_next
        )
        if self.combined_cond:
            base_cond = base_cond & self.combined_cond

        query = (
            frappe.qb.from_(self.ticket)
            .select(
                Count(self.ticket.name).as_("total_tickets"),
                Function("DATEDIFF", self.to_date_next, self.from_date).as_("days"),
            )
            .where(base_cond)
        )

        result = query.run(as_dict=True)
        total_tickets = result[0].total_tickets or 0
        days = result[0].days or 1
        return total_tickets / days
>>>>>>> 1e1cd602 (refactor: convert dashboard api to class and add QB support)


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
        order_by="count desc",
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
        order_by="count desc",
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
        order_by="count desc",
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


<<<<<<< HEAD
def get_trend_data(
    from_date, to_date, conds="", open_statuses=None, resolved_statuses=None
):
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
    from_date, to_date, conds="", open_statuses=None, resolved_statuses=None
):
    """
    Trend data for tickets in the dashboard. Ticket trend +SLA fulfilled
    """
    if len(open_statuses) == 1:
        open_statuses = f"('{open_statuses[0]}')"
    result = frappe.db.sql(
        f"""
            SELECT 
                DATE(creation) as date,
                COUNT(CASE WHEN status in {open_statuses} THEN name END) as open,
                COUNT(CASE WHEN status in {resolved_statuses} THEN name END) as closed,
                COUNT(CASE WHEN agreement_status = 'Fulfilled' THEN name END) as SLA_fulfilled
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
                "name": "SLA_fulfilled",
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
            AVG(CASE WHEN feedback_rating > 0 THEN feedback_rating END) * 5 as rating,
            COUNT(CASE WHEN feedback_rating > 0 THEN name END) as rated_tickets
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
=======
def get_pie_chart_config(
    data: list[dict[str, any]],
    title: str,
    subtitle: str,
    category_column: str,
    value_column: str,
) -> dict[str, any]:
>>>>>>> 1e1cd602 (refactor: convert dashboard api to class and add QB support)
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
<<<<<<< HEAD


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
=======
>>>>>>> 1e1cd602 (refactor: convert dashboard api to class and add QB support)
