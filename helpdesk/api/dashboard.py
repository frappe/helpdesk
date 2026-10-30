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


CAREVERSE_BRAND = "Careverse"
CAREVERSE_CARE_TEAM = "Careverse Care Team"


def _locked_brand(user=None):
    """Brand this user's dashboards are locked to, or None.
    Members of Careverse Care Team who are in no other team only see Careverse."""
    user = user or frappe.session.user
    teams = frappe.get_all("HD Team Member", filters={"user": user}, pluck="parent")
    if teams and set(teams) == {CAREVERSE_CARE_TEAM}:
        return CAREVERSE_BRAND
    return None


@frappe.whitelist()
@agent_only
def get_dashboard_data(
    dashboard_type: str, filters: dict[str, any] = None
) -> list[dict[str, any]] | None:
    """
    Get dashboard data based on the type and date range.
    """
    user = frappe.session.user
    is_manager = "Agent Manager" in frappe.get_roles(user) or bool(_locked_brand(user))

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
    if _locked_brand(user):
        agent = None
        team = None

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
        self.county = filters.get("county")
        self.support_level = filters.get("support_level")

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
        _brand = _locked_brand()
        if _brand:
            conds.append(self.ticket.brand == _brand)
        if self.team:
            conds.append(self.ticket.agent_group == self.team)
        if self.agent:
            # Pass args to Function(...) directly. ParameterizedFunction is not callable.
            conds.append(
                Function(
                    "JSON_SEARCH", self.ticket._assign, "one", self.agent
                ).isnotnull()
            )
        if self.county:
            conds.append(self.ticket.county == self.county)
        if self.support_level:
            conds.append(self.ticket.support_level == self.support_level)
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
            self.get_sla_breach_count(),
            self.get_sla_breach_percent(),
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

        target_pct = frappe.db.get_single_value("HD Settings", "sla_target_percentage") or 90

        return {
            "title": _("% SLA Fulfilled"),
            "value": current_pct,
            "suffix": "%",
            "delta": current_pct - target_pct,
            "deltaSuffix": "% vs {0}% target".format(target_pct),
            "tooltip": _("% of tickets created that were resolved within SLA. Target: {0}%").format(target_pct),
        }

    def get_sla_breach_count(self):
        """
        SLA breach across ALL tickets in the period (not just resolved ones),
        since a ticket is breached the moment agreement_status flips to
        'Failed', regardless of whether it has since been closed out.
        """
        extra_cond = self.ticket.agreement_status == "Failed"
        current_breached, prev_breached = self.get_metric_data(
            self.ticket.name, Count, extra_cond
        )
        current_total, prev_total = self.get_metric_data(self.ticket.name, Count)

        current_pct = (current_breached / current_total * 100) if current_total else 0
        prev_pct = (prev_breached / prev_total * 100) if prev_total else 0

        return {
            "title": _("Tickets Breached"),
            "value": current_breached,
            "delta": current_breached - prev_breached,
            "negativeIsBetter": True,
            "tooltip": _("Number of tickets that have breached SLA (agreement_status = Failed), regardless of current status"),
        }

    def get_sla_breach_percent(self):
        extra_cond = self.ticket.agreement_status == "Failed"
        current_breached, prev_breached = self.get_metric_data(
            self.ticket.name, Count, extra_cond
        )
        current_total, prev_total = self.get_metric_data(self.ticket.name, Count)

        current_pct = (current_breached / current_total * 100) if current_total else 0
        prev_pct = (prev_breached / prev_total * 100) if prev_total else 0

        return {
            "title": _("SLA Breach %"),
            "value": current_pct,
            "suffix": "%",
            "delta": current_pct - prev_pct,
            "deltaSuffix": "%",
            "negativeIsBetter": True,
            "tooltip": _("% of all tickets in this period that have breached SLA"),
        }

    def get_avg_first_response_time(self):
        extra_cond = self.ticket.first_responded_on.isnotnull()
        current, prev = self.get_metric_data(
            self.ticket.first_response_time / 3600, Avg, extra_cond
        )

        target_hours = frappe.db.get_single_value("HD Settings", "first_response_target_hours") or 4

        return {
            "title": _("Avg. First Response"),
            "value": current,
            "suffix": " " + _("hrs"),
            "delta": current - target_hours,
            "deltaSuffix": " {0} {1}".format(_("hrs vs"), _("{0} hrs target").format(target_hours)),
            "negativeIsBetter": True,
            "tooltip": _("Avg. time taken to first respond to a ticket. Target: {0} hrs").format(target_hours),
        }

    def get_avg_resolution_time(self):
        extra_cond = (
            self.ticket.status.isin(self.resolved_statuses)
            if self.resolved_statuses
            else None
        )
        value_expr = Function("CEIL", self.ticket.resolution_time / 86400)
        current, prev = self.get_metric_data(value_expr, Avg, extra_cond)

        target_days = frappe.db.get_single_value("HD Settings", "resolution_target_days") or 3

        return {
            "title": _("Avg. Resolution"),
            "value": current,
            "suffix": " " + _("days"),
            "delta": current - target_days,
            "deltaSuffix": " {0}".format(_("days vs {0} days target").format(target_days)),
            "negativeIsBetter": True,
            "tooltip": _("Avg. time taken to resolve a ticket. Target: {0} days").format(target_days),
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
    if _locked_brand():
        filters["brand"] = _locked_brand()
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


# ------------------------------------------------------------------ #
# County / Tier Dashboard                                              #
# ------------------------------------------------------------------ #


@frappe.whitelist()
@agent_only
def get_county_dashboard_data(
    from_date: str = None,
    to_date: str = None,
    county: str = None,
    support_level: str = None,
) -> dict[str, any]:
    """
    Get all data needed for the County / Tier dashboard in one call.
    """
    if not from_date:
        from_date = frappe.utils.add_days(frappe.utils.nowdate(), -30)
    if not to_date:
        to_date = frappe.utils.nowdate()

    filters = {
        "creation": ["between", [from_date, to_date]],
    }
    if county:
        filters["county"] = county
    if support_level:
        filters["support_level"] = support_level
    if _locked_brand():
        filters["brand"] = _locked_brand()

    _filters = frappe._dict(
        from_date=from_date,
        to_date=to_date,
        team=None,
        agent=None,
        county=county,
        support_level=support_level,
    )
    dashboard = HelpdeskDashboard(_filters)

    return {
        "number_cards": dashboard.get_number_card_data(),
        "county_chart": get_county_chart_data(filters),
        "support_level_chart": get_support_level_chart_data(filters),
        "priority_chart": get_ticket_priority_chart_data(from_date, to_date, filters),
        "type_chart": get_ticket_type_chart_data(from_date, to_date, filters),
        "channel_chart": get_ticket_channel_chart_data(from_date, to_date, filters),
        "implementers": [] if _locked_brand() else get_county_implementers(county),
    }


def get_county_chart_data(filters: dict[str, any] = None) -> dict[str, any]:
    """Tickets grouped by county."""
    result = frappe.get_all(
        HD_TICKET,
        fields=["county", COUNT_NAME],
        filters=filters,
        group_by="county",
        order_by=COUNT_DESC,
    )
    for r in result:
        if not r.county:
            r.county = _("No County")

    if len(result) < 7:
        return get_pie_chart_config(
            result,
            _("Tickets by County"),
            _("Percentage of Total Tickets by County"),
            "county",
            "count",
        )
    else:
        return get_bar_chart_config(
            result,
            _("Tickets by County"),
            _("Total Tickets by County"),
            {"key": "county", "type": "category", "title": "County", "timeGrain": "day"},
            "Tickets",
            [{"name": "count", "type": "bar"}],
        )


def get_support_level_chart_data(filters: dict[str, any] = None) -> dict[str, any]:
    """Tickets grouped by support level / tier (L0/L1/L2/L3)."""
    result = frappe.get_all(
        HD_TICKET,
        fields=["support_level", COUNT_NAME],
        filters=filters,
        group_by="support_level",
        order_by=COUNT_DESC,
    )
    for r in result:
        if not r.support_level:
            r.support_level = _("Unassigned")

    return get_pie_chart_config(
        result,
        _("Tickets by Support Level"),
        _("Percentage of Total Tickets by Tier"),
        "support_level",
        "count",
    )


def get_county_implementers(county: str = None) -> list[dict[str, any]]:
    """
    Derive, for each county, which teams and agents are actually assigned
    to tickets in that county (based on real ticket data), since a static
    county -> team mapping doesn't reliably exist across all counties.
    """
    filters = {"county": ["is", "set"]}
    if county:
        filters["county"] = county

    tickets = frappe.get_all(
        "HD Ticket",
        filters=filters,
        fields=["county", "agent_group", "_assign"],
    )

    county_data: dict[str, dict] = {}
    for t in tickets:
        c = t.county
        entry = county_data.setdefault(c, {"teams": set(), "agents": set()})
        if t.agent_group:
            entry["teams"].add(t.agent_group)
        if t._assign:
            import json
            try:
                assigned = json.loads(t._assign)
                for user in assigned:
                    entry["agents"].add(user)
            except (ValueError, TypeError):
                pass

    result = []
    for c, entry in county_data.items():
        agent_details = []
        if entry["agents"]:
            agent_details = frappe.get_all(
                "HD Agent",
                filters={"user": ["in", list(entry["agents"])]},
                fields=["user", "agent_name", "is_active"],
            )
        result.append({
            "county": c,
            "teams": sorted(entry["teams"]),
            "implementers": agent_details,
        })

    result.sort(key=lambda r: r["county"])
    return result
