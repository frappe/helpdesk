import math
import operator
from functools import reduce

import frappe
from frappe import _
from frappe.query_builder import DocType
from frappe.query_builder.functions import Avg, Count, Function
from pypika import Case

from helpdesk.utils import agent_only, is_frappe_version

HD_TICKET = "HD Ticket"

COUNT_NAME = (
    {"COUNT": "name", "as": "count"}
    if is_frappe_version("16", above=True)
    else "count(name) as count"
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
        from_date = frappe.utils.add_days(frappe.utils.nowdate(), -29)
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
    elif dashboard_type == "tags":
        from helpdesk.api.dashboard_tags import TagDashboard

        return TagDashboard(_filters).get_tag_chart_data()


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

        # compare with the same number of days right before this period
        self.period_days = frappe.utils.date_diff(self.to_date, self.from_date) + 1
        self.prev_from_date = frappe.utils.add_days(self.from_date, -self.period_days)
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

    def _get_case(self, start, end, value, func, extra_cond=None, date_field=None):
        date_field = date_field or self.ticket.creation
        cond = (date_field >= start) & (date_field < end)
        if extra_cond:
            cond = cond & extra_cond
        if self.combined_cond:
            cond = cond & self.combined_cond

        return func(Case().when(cond, value).else_(None))

    def get_metric_data(self, value, func, extra_cond=None, date_field=None):
        current_expr = self._get_case(
            self.from_date, self.to_date_next, value, func, extra_cond, date_field
        )
        prev_expr = self._get_case(
            self.prev_from_date, self.from_date, value, func, extra_cond, date_field
        )

        query = frappe.qb.from_(self.ticket).select(
            current_expr.as_("current"), prev_expr.as_("prev")
        )
        result = query.run(as_dict=True)
        # average stays None when the period has no tickets
        return result[0].current, result[0].prev

    def round_or_none(self, value, digits=1):
        return None if value is None else round(value, digits)

    def get_change(self, current, prev, digits=1):
        # an empty period on either side leaves nothing to compare
        if current is None or prev is None:
            return None
        return round(current - prev, digits)

    def get_number_card_data(self):
        cards = [
            self.get_ticket_count(),
            self.get_sla_fulfilled_count(),
            self.get_avg_first_response_time(),
            self.get_avg_resolution_time(),
            self.get_avg_feedback_score(),
        ]
        caption = self.get_delta_caption()
        for card in cards:
            if card["delta"] is not None:
                card["deltaCaption"] = caption
        return cards

    def get_delta_caption(self):
        if self.period_days > 1:
            return _("vs prev. {0} days").format(self.period_days)
        if frappe.utils.getdate(self.to_date) == frappe.utils.getdate():
            return _("vs yesterday")
        return _("vs prev. day")

    def get_ticket_count(self):
        current, prev = self.get_metric_data(self.ticket.name, Count)
        # no previous period to compare against: no delta, not a 0% change
        delta = round((current - prev) / prev * 100) if prev else None

        return {
            "title": _("Tickets"),
            "value": current,
            "delta": delta,
            "deltaSuffix": "%",
            "negativeIsBetter": True,
            "tooltip": _("Total number of tickets created"),
        }

    def get_sla_fulfilled_count(self):
        # the numerator must stay a subset of the denominator, else the
        # percentage can exceed 100 (a response-only SLA marks an open ticket
        # Fulfilled, which no resolved-status filter would count)
        status_cond = self.ticket.sla.isnotnull()
        if self.resolved_statuses:
            status_cond = status_cond & self.ticket.status.isin(self.resolved_statuses)
        current_fulfilled, prev_fulfilled = self.get_metric_data(
            self.ticket.name,
            Count,
            status_cond & (self.ticket.agreement_status == "Fulfilled"),
        )
        current_total, prev_total = self.get_metric_data(
            self.ticket.name, Count, status_cond
        )

        # no resolved tickets means there is no SLA % to show
        current_pct = (
            (current_fulfilled / current_total * 100) if current_total else None
        )
        prev_pct = (prev_fulfilled / prev_total * 100) if prev_total else None

        return {
            "title": _("% SLA Fulfilled"),
            "value": self.round_or_none(current_pct, 0),
            "suffix": "%",
            "delta": self.get_change(current_pct, prev_pct, 0),
            "deltaSuffix": "%",
            "tooltip": _("% of tickets created that were resolved within SLA"),
        }

    def get_avg_first_response_time(self):
        extra_cond = (
            self.ticket.sla.isnotnull() & self.ticket.first_responded_on.isnotnull()
        )
        current, prev = self.get_metric_data(
            self.ticket.first_response_time / 3600, Avg, extra_cond
        )

        return {
            "title": _("Avg. First Response"),
            "value": self.round_or_none(current),
            "suffix": " " + _("hrs"),
            "delta": self.get_change(current, prev),
            "deltaSuffix": " " + _("hrs"),
            "negativeIsBetter": True,
            "tooltip": _("Avg. time taken to first respond to a ticket"),
        }

    def get_avg_resolution_time(self):
        extra_cond = self.ticket.sla.isnotnull()
        if self.resolved_statuses:
            extra_cond = extra_cond & self.ticket.status.isin(self.resolved_statuses)
        value_expr = Function("CEIL", self.ticket.resolution_time / 86400)
        current, prev = self.get_metric_data(value_expr, Avg, extra_cond)

        return {
            "title": _("Avg. Resolution"),
            "value": self.round_or_none(current),
            "suffix": " " + _("days"),
            "delta": self.get_change(current, prev),
            "deltaSuffix": " " + _("days"),
            "negativeIsBetter": True,
            "tooltip": _("Avg. time taken to resolve a ticket"),
        }

    def get_avg_feedback_score(self):
        # Feedback belongs to the period a ticket was resolved in, not when it
        # was raised, so include every ticket resolved within the date range
        # regardless of its creation date.
        extra_cond = self.ticket.feedback_rating > 0
        current, prev = self.get_metric_data(
            self.ticket.feedback_rating * 5,
            Avg,
            extra_cond,
            date_field=self.ticket.resolution_date,
        )

        return {
            "title": _("Avg. Feedback Rating"),
            "value": self.round_or_none(current),
            "suffix": "/5",
            "delta": self.get_change(current, prev),
            "deltaSuffix": " " + _("stars"),
            "tooltip": _("Avg. feedback rating for tickets resolved in this period"),
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
        sla_resolved_cond = self.ticket.sla.isnotnull() & self.ticket.status.isin(
            self.resolved_statuses
        )

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
                (
                    Count(
                        Case()
                        .when(
                            sla_resolved_cond
                            & (self.ticket.agreement_status == "Fulfilled"),
                            self.ticket.name,
                        )
                        .else_(None)
                    )
                    * 100
                    / Count(
                        Case().when(sla_resolved_cond, self.ticket.name).else_(None)
                    )
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
            "ticket_trend",
            _("Ticket Trend"),
            subtitle,
            "date",
            {"type": "time", "title": "Date", "timeGrain": "day"},
            _("Tickets"),
            [closed_status, open_status],
            y2=sla_fulfilled_status,
            seriesConfig={
                sla_fulfilled_status: {"type": "line", "showDataPoints": True}
            },
            stacked=True,
            y2Axis={"title": "% SLA", "min": 0, "max": 100},
        )

    def get_feedback_trend_data(self):
        rating = "Rating"
        rated_tickets = "Rated Tickets"

        # Plot feedback against the resolution date so this trend matches the
        # number-card average (get_avg_feedback_score), which also keys feedback
        # off resolution_date rather than creation.
        date_field = self.ticket.resolution_date

        base_cond = (date_field > self.from_date) & (date_field < self.to_date_next)
        if self.combined_cond:
            base_cond = base_cond & self.combined_cond

        query = (
            frappe.qb.from_(self.ticket)
            .select(
                Function("DATE", date_field).as_("date"),
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
            .groupby(Function("DATE", date_field))
            .orderby(Function("DATE", date_field))
        )

        result = query.run(as_dict=True)

        # Avg rating query
        avg_query = (
            frappe.qb.from_(self.ticket)
            .select((Avg(self.ticket.feedback_rating) * 5).as_("avg_rating"))
            .where(
                (date_field.between(self.from_date, self.to_date_next))
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
            "feedback_trend",
            _("Feedback Trend"),
            subtitle,
            "date",
            {"type": "time", "title": "Date", "timeGrain": "day"},
            _("Rated Tickets"),
            rated_tickets,
            y2=rating,
            seriesConfig={
                rating: {"type": "line", "showDataPoints": True, "color": "#48BB74"}
            },
            y2Axis={"title": _("Rating"), "min": 0, "max": 5},
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
            "tickets_by_team",
            _("Tickets by Team"),
            _("Percentage of total tickets by team"),
            "team",
            "count",
        )
    else:
        return get_bar_chart_config(
            result,
            "tickets_by_team",
            _("Tickets by Team"),
            _("Total tickets by team"),
            "team",
            {"type": "category", "title": "Team"},
            "Tickets",
            "count",
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
            "tickets_by_type",
            _("Tickets by Type"),
            _("Percentage of total tickets by type"),
            "type",
            "count",
        )
    else:
        return get_bar_chart_config(
            result,
            "tickets_by_type",
            _("Tickets by Type"),
            _("Total tickets by type"),
            "type",
            {"type": "category", "title": "Type"},
            "Tickets",
            "count",
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
            "tickets_by_priority",
            _("Tickets by Priority"),
            _("Percentage of total tickets by priority"),
            "priority",
            "count",
        )
    else:
        return get_bar_chart_config(
            result,
            "tickets_by_priority",
            _("Tickets by Priority"),
            _("Total tickets by priority"),
            "priority",
            {"type": "category", "title": "Priority"},
            "Tickets",
            "count",
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
        "tickets_by_channel",
        _("Tickets by Channel"),
        _("Percentage of total tickets by channel"),
        "channel",
        "count",
    )


def get_pie_chart_config(
    data: list[dict[str, any]],
    key: str,
    title: str,
    subtitle: str,
    category_column: str,
    value_column: str,
) -> dict[str, any]:
    return {
        "type": "donut",
        "data": data,
        # stable identifier for the client, `title` is translated and cannot be matched on
        "key": key,
        "title": title,
        "subtitle": subtitle,
        "category": category_column,
        "value": value_column,
    }


def get_bar_chart_config(
    data: list[dict[str, any]],
    key: str,
    title: str,
    subtitle: str,
    x: str,
    x_axis: dict[str, any],
    y_axis_title: str,
    y: str | list[str],
    **kwargs: dict[str, any],
) -> dict[str, any]:
    """frappe-ui BarChart props for a dashboard chart"""
    chart = {
        "type": "bar",
        "data": data,
        # stable identifier for the client, `title` is translated and cannot be matched on
        "key": key,
        "title": title,
        "subtitle": subtitle,
        "x": x,
        "y": y,
        "xAxis": x_axis,
        # ticket counts are whole numbers so keep the axis on whole steps
        "yAxis": {"title": y_axis_title, "echartOptions": {"minInterval": 1}},
        **kwargs,
    }
    if "y2Axis" in kwargs:
        chart["yAxis"]["max"] = get_y_axis_max(data, y, kwargs.get("stacked"))
    return chart


def get_y_axis_max(data: list[dict[str, any]], y: str | list[str], stacked: bool):
    """round the peak up to a multiple of 5 so the y2 axis gets clean steps"""
    columns = [y] if isinstance(y, str) else y
    combine = sum if stacked else max
    peak = max(
        (combine(row[column] or 0 for column in columns) for row in data), default=0
    )
    return max(5, math.ceil(peak / 5) * 5)
