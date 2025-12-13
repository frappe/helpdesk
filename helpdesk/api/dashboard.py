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

    def get_metric_data(self, value, func, extra_cond=None):
        current_expr = self._get_case(
            self.from_date, self.to_date_next, value, func, extra_cond
        )
        prev_expr = self._get_case(
            self.prev_from_date, self.from_date, value, func, extra_cond
        )

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

        status_cond = (
            self.ticket.status.isin(self.resolved_statuses)
            if self.resolved_statuses
            else None
        )
        current_total, prev_total = self.get_metric_data(
            self.ticket.name, Count, status_cond
        )

        current_pct = (current_fulfilled / current_total * 100) if current_total else 0
        prev_pct = (prev_fulfilled / prev_total * 100) if prev_total else 0

        return {
            "title": _("% SLA Fulfilled"),
            "value": current_pct,
            "suffix": "%",
            "delta": current_pct - prev_pct,
            "deltaSuffix": "%",
            "tooltip": _("% of tickets created that were resolved within SLA"),
        }

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

    def get_avg_feedback_score(self):
        extra_cond = self.ticket.feedback_rating > 0
        current, prev = self.get_metric_data(
            self.ticket.feedback_rating, Avg, extra_cond
        )

        return {
            "title": _("Avg. Feedback Rating"),
            "value": current * 5,
            "suffix": "/5",
            "delta": (current - prev) * 5,
            "deltaSuffix": " " + _("stars"),
            "tooltip": _("Avg. feedback rating for the tickets resolved"),
        }

    def get_trend_data(self):
        return [
            self.get_ticket_trend_data(),
            self.get_feedback_trend_data(),
        ]

    def get_ticket_trend_data(self):
        open_status = "Open"
        closed_status = "Closed"
        sla_fulfilled_status = "SLA Fulfilled"

        base_cond = (self.ticket.creation > self.from_date) & (
            self.ticket.creation < self.to_date_next
        )
        if self.combined_cond:
            base_cond = base_cond & self.combined_cond

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

    def get_feedback_trend_data(self):
        rating = "Rating"
        rated_tickets = "Rated Tickets"

        base_cond = (self.ticket.creation > self.from_date) & (
            self.ticket.creation < self.to_date_next
        )
        if self.combined_cond:
            base_cond = base_cond & self.combined_cond

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

        avg_rating_result = avg_query.run(pluck=True)
        avg_rating = (
            avg_rating_result[0] if avg_rating_result and avg_rating_result[0] else 0
        )

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


@frappe.whitelist()
@agent_only
def get_status_card_data(filters: dict[str, any] = None) -> list[dict[str, any]]:
    """
    Get status card data for Freshdesk-style dashboard.
    Returns counts for: Unresolved, Overdue, Due Today, Open, On Hold, Unassigned
    """
    user = frappe.session.user
    is_manager = "Agent Manager" in frappe.get_roles(user)

    if filters and not is_manager and (
        filters.get("team")
        or filters.get("agent") not in (None, user, "@me")
        or filters.get("owner") not in (None, user, "@me")
    ):
        frappe.throw(
            _("You are not allowed to view this dashboard data."),
            frappe.PermissionError,
        )

    ticket = DocType("HD Ticket")
    today = frappe.utils.nowdate()

    # Get date range from filters
    from_date = filters.get("from_date") if filters else None
    to_date = filters.get("to_date") if filters else None
    
    # If no dates provided, default to all time
    if from_date and to_date:
        to_date_next = frappe.utils.add_days(to_date, 1)
    else:
        from_date = None
        to_date_next = None

    # Get open statuses
    open_statuses = frappe.get_all(
        "HD Ticket Status",
        filters={"category": "Open"},
        pluck="name",
    )

    # Build base conditions
    base_conds = []
    # Add date filter if provided
    if from_date and to_date_next:
        base_conds.append(ticket.creation >= from_date)
        base_conds.append(ticket.creation < to_date_next)
    
    if filters:
        if filters.get("team"):
            base_conds.append(ticket.agent_group == filters.get("team"))
        if filters.get("agent"):
            agent = filters.get("agent")
            if agent == "@me":
                agent = user
            base_conds.append(
                Function("JSON_SEARCH", ticket._assign, "one", agent).isnotnull()
            )
        if filters.get("owner"):
            owner = filters.get("owner")
            if owner == "@me":
                owner = user
            base_conds.append(ticket.owner == owner)

    def get_count(extra_cond=None):
        query = frappe.qb.from_(ticket).select(Count(ticket.name).as_("count"))
        for cond in base_conds:
            query = query.where(cond)
        if extra_cond is not None:
            query = query.where(extra_cond)
        result = query.run(as_dict=True)
        return result[0].count if result else 0

    # Unresolved: All tickets in open statuses
    unresolved_cond = ticket.status.isin(open_statuses) if open_statuses else None
    unresolved = get_count(unresolved_cond)

    # Overdue: Open tickets past their resolution_by date
    overdue_cond = (
        ticket.status.isin(open_statuses) if open_statuses else ticket.status == "Open"
    ) & (ticket.resolution_by < today) & (ticket.resolution_by.isnotnull())
    overdue = get_count(overdue_cond)

    # Due Today: Open tickets with resolution_by = today
    due_today_cond = (
        ticket.status.isin(open_statuses) if open_statuses else ticket.status == "Open"
    ) & (ticket.resolution_by == today)
    due_today = get_count(due_today_cond)

    # Open: Tickets with status "Open"
    open_count = get_count(ticket.status == "Open")

    # On Hold: Tickets with status containing "hold" or "pending"
    on_hold_statuses = frappe.get_all(
        "HD Ticket Status",
        filters=[["name", "like", "%hold%"]],
        pluck="name",
    )
    on_hold_statuses += frappe.get_all(
        "HD Ticket Status",
        filters=[["name", "like", "%pending%"]],
        pluck="name",
    )
    on_hold = get_count(ticket.status.isin(on_hold_statuses)) if on_hold_statuses else 0

    # Unassigned: Open tickets with no assignee
    unassigned_cond = (
        ticket.status.isin(open_statuses) if open_statuses else ticket.status == "Open"
    ) & ((ticket._assign.isnull()) | (ticket._assign == "[]"))
    unassigned = get_count(unassigned_cond)

    # Resolved: Tickets with resolved status (category = Resolved, but not "Closed")
    resolved_statuses = frappe.get_all(
        "HD Ticket Status",
        filters={"category": "Resolved"},
        pluck="name",
    )
    # Exclude "Closed" from resolved for separate counting
    resolved_only_statuses = [s for s in resolved_statuses if s != "Closed"] if resolved_statuses else []
    resolved_cond = ticket.status.isin(resolved_only_statuses) if resolved_only_statuses else None
    resolved_count = get_count(resolved_cond) if resolved_cond else 0

    # Closed: Tickets with status "Closed" specifically
    closed_cond = ticket.status == "Closed"
    closed_count = get_count(closed_cond)

    # Pending: Tickets with status containing "pending"
    pending_statuses = frappe.get_all(
        "HD Ticket Status",
        filters=[["name", "like", "%pending%"]],
        pluck="name",
    )
    pending_count = get_count(ticket.status.isin(pending_statuses)) if pending_statuses else 0

    # Today's Tickets: Tickets created today
    todays_tickets_cond = Function("DATE", ticket.creation) == today
    todays_tickets = get_count(todays_tickets_cond)

    # Format filters to match the query logic
    resolved_filter = {"status": ["in", resolved_only_statuses]} if resolved_only_statuses else {}
    closed_filter = {"status": "Closed"}
    pending_filter = {"status": ["in", pending_statuses]} if pending_statuses else {}
    
    return [
        {"label": _("Open"), "count": open_count, "status_filter": {"status": "Open"}, "color": "#318AD8"},
        {"label": _("Resolved"), "count": resolved_count, "status_filter": resolved_filter, "color": "#48BB78"},
        {"label": _("Closed"), "count": closed_count, "status_filter": closed_filter, "color": "#9F7AEA"},
        {"label": _("Pending"), "count": pending_count, "status_filter": pending_filter, "color": "#F6AD55"},
        {"label": _("Today's Tickets"), "count": todays_tickets, "status_filter": {"today": True}, "color": "#F6AD55"},
    ]


@frappe.whitelist()
@agent_only
def get_today_trend_data(filters: dict[str, any] = None) -> dict[str, any]:
    """
    Get hourly ticket trend data for today and yesterday.
    """
    user = frappe.session.user
    is_manager = "Agent Manager" in frappe.get_roles(user)

    if filters and not is_manager and (
        filters.get("team")
        or filters.get("agent") not in (None, user, "@me")
        or filters.get("owner") not in (None, user, "@me")
    ):
        frappe.throw(
            _("You are not allowed to view this dashboard data."),
            frappe.PermissionError,
        )

    ticket = DocType("HD Ticket")
    today = frappe.utils.nowdate()
    yesterday = frappe.utils.add_days(today, -1)
    tomorrow = frappe.utils.add_days(today, 1)

    # Build base conditions
    base_conds = []
    if filters:
        if filters.get("team"):
            base_conds.append(ticket.agent_group == filters.get("team"))
        if filters.get("agent"):
            agent = filters.get("agent")
            if agent == "@me":
                agent = user
            base_conds.append(
                Function("JSON_SEARCH", ticket._assign, "one", agent).isnotnull()
            )
        if filters.get("owner"):
            owner = filters.get("owner")
            if owner == "@me":
                owner = user
            base_conds.append(ticket.owner == owner)

    def get_hourly_data(date_start, date_end):
        query = (
            frappe.qb.from_(ticket)
            .select(
                Function("HOUR", ticket.creation).as_("hour"),
                Count(ticket.name).as_("count"),
            )
            .where(ticket.creation >= date_start)
            .where(ticket.creation < date_end)
            .groupby(Function("HOUR", ticket.creation))
            .orderby(Function("HOUR", ticket.creation))
        )
        for cond in base_conds:
            query = query.where(cond)
        return query.run(as_dict=True)

    today_data = get_hourly_data(today, tomorrow)
    yesterday_data = get_hourly_data(yesterday, today)

    # Get summary metrics
    resolved_statuses = frappe.get_all(
        "HD Ticket Status",
        filters={"category": "Resolved"},
        pluck="name",
    )

    # Received today
    received_query = (
        frappe.qb.from_(ticket)
        .select(Count(ticket.name).as_("count"))
        .where(ticket.creation >= today)
        .where(ticket.creation < tomorrow)
    )
    for cond in base_conds:
        received_query = received_query.where(cond)
    received_result = received_query.run(as_dict=True)
    received = received_result[0].count if received_result else 0

    # Avg first response (in hours)
    avg_response_query = (
        frappe.qb.from_(ticket)
        .select(Avg(ticket.first_response_time / 3600).as_("avg"))
        .where(ticket.creation >= today)
        .where(ticket.creation < tomorrow)
        .where(ticket.first_responded_on.isnotnull())
    )
    for cond in base_conds:
        avg_response_query = avg_response_query.where(cond)
    avg_response_result = avg_response_query.run(as_dict=True)
    avg_first_response = round(avg_response_result[0].avg or 0, 1)

    # Resolution rate (resolved / total * 100)
    total_query = (
        frappe.qb.from_(ticket)
        .select(Count(ticket.name).as_("count"))
        .where(ticket.creation >= today)
        .where(ticket.creation < tomorrow)
    )
    for cond in base_conds:
        total_query = total_query.where(cond)
    total_result = total_query.run(as_dict=True)
    total = total_result[0].count if total_result else 0

    resolved_query = (
        frappe.qb.from_(ticket)
        .select(Count(ticket.name).as_("count"))
        .where(ticket.creation >= today)
        .where(ticket.creation < tomorrow)
        .where(ticket.status.isin(resolved_statuses) if resolved_statuses else ticket.status == "Closed")
    )
    for cond in base_conds:
        resolved_query = resolved_query.where(cond)
    resolved_result = resolved_query.run(as_dict=True)
    resolved = resolved_result[0].count if resolved_result else 0

    resolution_rate = round((resolved / total * 100) if total > 0 else 0, 0)

    return {
        "today": today_data,
        "yesterday": yesterday_data,
        "summary": {
            "received": received,
            "avgFirstResponse": avg_first_response,
            "resolutionRate": resolution_rate,
        },
    }


@frappe.whitelist()
@agent_only
def get_unresolved_grouped_data(filters: dict[str, any] = None) -> list[dict[str, any]]:
    """
    Get unresolved tickets grouped by team.
    """
    user = frappe.session.user
    is_manager = "Agent Manager" in frappe.get_roles(user)

    if filters and not is_manager and (
        filters.get("team")
        or filters.get("agent") not in (None, user, "@me")
        or filters.get("owner") not in (None, user, "@me")
    ):
        frappe.throw(
            _("You are not allowed to view this dashboard data."),
            frappe.PermissionError,
        )

    open_statuses = frappe.get_all(
        "HD Ticket Status",
        filters={"category": "Open"},
        pluck="name",
    )

    base_filters = {
        "status": ["in", open_statuses] if open_statuses else ["=", "Open"],
    }
    if filters:
        if filters.get("team"):
            base_filters["agent_group"] = filters.get("team")
        if filters.get("agent"):
            agent = filters.get("agent")
            if agent == "@me":
                agent = user
            base_filters["_assign"] = ["like", f"%{agent}%"]
        if filters.get("owner"):
            owner = filters.get("owner")
            if owner == "@me":
                owner = user
            base_filters["owner"] = owner

    result = frappe.get_all(
        HD_TICKET,
        fields=["agent_group as name", COUNT_NAME],
        filters=base_filters,
        group_by="agent_group",
        order_by=COUNT_DESC,
    )

    for r in result:
        if not r.name:
            r.name = _("Unassigned")

    return result


@frappe.whitelist()
@agent_only
def get_satisfaction_data(filters: dict[str, any] = None) -> dict[str, any]:
    """
    Get customer satisfaction breakdown.
    """
    user = frappe.session.user
    is_manager = "Agent Manager" in frappe.get_roles(user)

    if filters and not is_manager and (
        filters.get("team")
        or filters.get("agent") not in (None, user, "@me")
        or filters.get("owner") not in (None, user, "@me")
    ):
        frappe.throw(
            _("You are not allowed to view this dashboard data."),
            frappe.PermissionError,
        )

    ticket = DocType("HD Ticket")

    # Build base conditions
    base_conds = [ticket.feedback_rating > 0]
    if filters:
        if filters.get("team"):
            base_conds.append(ticket.agent_group == filters.get("team"))
        if filters.get("agent"):
            agent = filters.get("agent")
            if agent == "@me":
                agent = user
            base_conds.append(
                Function("JSON_SEARCH", ticket._assign, "one", agent).isnotnull()
            )
        if filters.get("owner"):
            owner = filters.get("owner")
            if owner == "@me":
                owner = user
            base_conds.append(ticket.owner == owner)
        if filters.get("from_date"):
            base_conds.append(ticket.creation >= filters.get("from_date"))
        if filters.get("to_date"):
            base_conds.append(ticket.creation <= filters.get("to_date"))

    # Total responses
    total_query = frappe.qb.from_(ticket).select(Count(ticket.name).as_("count"))
    for cond in base_conds:
        total_query = total_query.where(cond)
    total_result = total_query.run(as_dict=True)
    total = total_result[0].count if total_result else 0

    if total == 0:
        return {
            "responsesReceived": 0,
            "positive": 0,
            "neutral": 0,
            "negative": 0,
        }

    # Positive (rating >= 0.8, i.e., 4-5 stars on 5-star scale)
    positive_query = frappe.qb.from_(ticket).select(Count(ticket.name).as_("count"))
    for cond in base_conds:
        positive_query = positive_query.where(cond)
    positive_query = positive_query.where(ticket.feedback_rating >= 0.8)
    positive_result = positive_query.run(as_dict=True)
    positive = positive_result[0].count if positive_result else 0

    # Neutral (rating between 0.5 and 0.8, i.e., 3 stars)
    neutral_query = frappe.qb.from_(ticket).select(Count(ticket.name).as_("count"))
    for cond in base_conds:
        neutral_query = neutral_query.where(cond)
    neutral_query = neutral_query.where(
        (ticket.feedback_rating >= 0.5) & (ticket.feedback_rating < 0.8)
    )
    neutral_result = neutral_query.run(as_dict=True)
    neutral = neutral_result[0].count if neutral_result else 0

    # Negative (rating < 0.5, i.e., 1-2 stars)
    negative_query = frappe.qb.from_(ticket).select(Count(ticket.name).as_("count"))
    for cond in base_conds:
        negative_query = negative_query.where(cond)
    negative_query = negative_query.where(ticket.feedback_rating < 0.5)
    negative_result = negative_query.run(as_dict=True)
    negative = negative_result[0].count if negative_result else 0

    return {
        "responsesReceived": total,
        "positive": round(positive / total * 100) if total > 0 else 0,
        "neutral": round(neutral / total * 100) if total > 0 else 0,
        "negative": round(negative / total * 100) if total > 0 else 0,
    }
