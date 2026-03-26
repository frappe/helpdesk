from datetime import date, timedelta

import frappe
from frappe import _
from frappe.query_builder import DocType
from frappe.query_builder.functions import Avg, Count, Function
from frappe.utils import add_days, nowdate

from helpdesk.api.agent_home.utils import calculate_percentage_change
from helpdesk.api.analytics_utils import _apply_scope, get_avg_time_metric
from helpdesk.utils import agent_only

Scope = str  # Literal["agent", "customer", "contact"]

DT_FIELD_MAP = {
    "HD Customer": "customer",
    "Contact": "contact",
}


periods = {"last week": 7, "last month": 30, "last 3 months": 90, "last 6 months": 180}


def _resolve_scope(dt: str) -> str:
    if dt not in DT_FIELD_MAP:
        frappe.throw(_("Unsupported doctype '{0}' for ticket stats.").format(dt))
    return DT_FIELD_MAP[dt]


def _fill_date_series(from_date_str, to_date_str, rows: list) -> list:
    """Return a {date, count} list for every day in the range, filling 0 for missing days."""
    date_dict: dict[str, int] = {}
    cur = date.fromisoformat(str(from_date_str))
    end = date.fromisoformat(str(to_date_str))
    while cur <= end:
        date_dict[cur.isoformat()] = 0
        cur += timedelta(days=1)
    for row in rows:
        date_dict[str(row["date"])] = row["count"]
    return [{"date": d, "count": c} for d, c in sorted(date_dict.items())]


@frappe.whitelist()
@agent_only
def get_total_tickets(
    dt: str,
    dn: str,
    period: str = "last month",
) -> dict:
    return _get_total_tickets(_resolve_scope(dt), dn, period)


def _get_total_tickets(
    scope: Scope,
    value: str,
    period: str = "last month",
) -> dict:

    days = periods.get(period, 7)

    current_from = add_days(nowdate(), -(days - 1))
    current_to = nowdate()
    previous_from = add_days(nowdate(), -(2 * days - 1))
    previous_to = add_days(nowdate(), -days)

    def _query(from_date, to_date, group_by_date=False):
        Ticket = DocType("HD Ticket")
        creation_date = Function("DATE", Ticket.creation)
        to_date_plus_one = Function(
            "DATE_ADD", to_date, frappe.qb.terms.PseudoColumn("INTERVAL 1 DAY")
        )
        if group_by_date:
            q = (
                frappe.qb.from_(Ticket)
                .select(creation_date.as_("date"), Count(Ticket.name).as_("count"))
                .groupby(creation_date)
                .orderby(creation_date)
            )
        else:
            q = frappe.qb.from_(Ticket).select(Count(Ticket.name).as_("count"))
        q = q.where(Ticket.creation >= from_date).where(
            Ticket.creation < to_date_plus_one
        )
        q = _apply_scope(q, Ticket, scope, value)
        return q.run(as_dict=True)

    current_rows = _query(current_from, current_to, group_by_date=True)
    current_total = sum(row["count"] for row in current_rows)
    previous_total = (_query(previous_from, previous_to) or [{"count": 0}])[0]["count"]

    return {
        "data": _fill_date_series(current_from, current_to, current_rows),
        "total": current_total,
        "percentage_change": calculate_percentage_change(current_total, previous_total),
    }


@frappe.whitelist()
@agent_only
def get_feedback_received(
    dt: str,
    dn: str,
    period: str = "last month",
) -> dict:
    return _get_feedback_received(_resolve_scope(dt), dn, period)


def _get_feedback_received(
    scope: Scope,
    value: str,
    period: str = "last month",
) -> dict:
    from datetime import datetime

    from dateutil.relativedelta import relativedelta

    days = periods.get(period, 7)

    if days <= 7:
        bucket = "daily"
    elif days <= 90:
        bucket = "weekly"
    else:
        bucket = "monthly"

    current_from = add_days(nowdate(), -(days - 1))
    current_to = nowdate()
    previous_from = add_days(nowdate(), -(2 * days - 1))
    previous_to = add_days(nowdate(), -days)

    def _query(from_date, to_date, grouped=False):
        Ticket = DocType("HD Ticket")
        to_date_plus_one = Function(
            "DATE_ADD", to_date, frappe.qb.terms.PseudoColumn("INTERVAL 1 DAY")
        )
        if grouped:
            if bucket == "daily":
                key = Function("DATE", Ticket.creation)
                sort = key
            elif bucket == "weekly":
                key = Function("DATE_FORMAT", Ticket.creation, "%x-%v")
                sort = key
            else:
                key = Function("DATE_FORMAT", Ticket.creation, "%b %Y")
                sort = Function("DATE_FORMAT", Ticket.creation, "%Y%m")
            q = (
                frappe.qb.from_(Ticket)
                .select(key.as_("date"), Count(Ticket.name).as_("count"))
                .groupby(sort)
                .orderby(sort)
            )
        else:
            q = frappe.qb.from_(Ticket).select(
                Count(Ticket.name).as_("count"),
                (Avg(Ticket.feedback_rating) * 5).as_("average_rating"),
            )

        q = (
            q.where(Ticket.creation >= from_date)
            .where(Ticket.creation < to_date_plus_one)
            .where(Ticket.feedback_rating > 0)
        )
        q = _apply_scope(q, Ticket, scope, value)
        return q.run(as_dict=True, debug=True)

    current_rows = _query(current_from, current_to, grouped=True)

    summary = (_query(current_from, current_to) or [{"count": 0, "average_rating": 0}])[
        0
    ]
    average_rating = round(float(summary.get("average_rating") or 0), 1)

    now = datetime.now()
    if bucket == "daily":
        data = _fill_date_series(current_from, current_to, current_rows)
    elif bucket == "weekly":
        week_dict: dict[str, dict] = {}
        cur = date.fromisoformat(str(current_from))
        end = date.fromisoformat(str(current_to))
        cur -= timedelta(days=cur.weekday())
        while cur <= end:
            iso = cur.strftime("%G-%V")
            label = f"{cur.strftime('%b %-d')} – {(cur + timedelta(days=6)).strftime('%b %-d')}"
            week_dict[iso] = {"label": label, "count": 0}
            cur += timedelta(weeks=1)
        for row in current_rows:
            k = str(row["date"])
            if k in week_dict:
                week_dict[k]["count"] = row["count"]
        data = [{"date": v["label"], "count": v["count"]} for v in week_dict.values()]
    else:
        num_months = days // 30
        month_dict: dict[str, int] = {}
        for i in range(num_months - 1, -1, -1):
            m = now - relativedelta(months=i)
            month_dict[m.strftime("%b %Y")] = 0
        for row in current_rows:
            k = str(row["date"])
            if k in month_dict:
                month_dict[k] = row["count"]
        data = [{"date": label, "count": count} for label, count in month_dict.items()]

    current_total = sum(row["count"] for row in current_rows)
    previous_total = (_query(previous_from, previous_to) or [{"count": 0}])[0]["count"]
    percentage_change = calculate_percentage_change(current_total, previous_total)

    return {
        "data": data,
        "average": average_rating,
        "percentage_change": percentage_change,
    }


@frappe.whitelist()
@agent_only
def get_sla_violations(
    dt: str,
    dn: str,
    period: str = "last month",
) -> dict:
    return _get_sla_violations(_resolve_scope(dt), dn, period)


def _get_sla_violations(
    scope: Scope,
    value: str,
    period: str = "last month",
) -> dict:
    from datetime import datetime

    from dateutil.relativedelta import relativedelta

    days = periods.get(period, 7)

    # Option B: adaptive bucketing
    #   last week (7d)       → daily   → 7 bars
    #   last month (30d)     → weekly  → ~4 bars
    #   last 3 months (90d)  → weekly  → ~13 bars
    #   last 6 months (180d) → monthly → 6 bars
    if days <= 7:
        bucket = "daily"
    elif days <= 90:
        bucket = "weekly"
    else:
        bucket = "monthly"

    current_from = add_days(nowdate(), -(days - 1))
    current_to = nowdate()
    previous_from = add_days(nowdate(), -(2 * days - 1))
    previous_to = add_days(nowdate(), -days)

    def _query(from_date, to_date, grouped=False):
        Ticket = DocType("HD Ticket")
        to_date_plus_one = Function(
            "DATE_ADD", to_date, frappe.qb.terms.PseudoColumn("INTERVAL 1 DAY")
        )
        if grouped:
            if bucket == "daily":
                key = Function("DATE", Ticket.creation)
                sort = key
            elif bucket == "weekly":
                # ISO year-week e.g. "2026-12"
                key = Function("DATE_FORMAT", Ticket.creation, "%x-%v")
                sort = key
            else:  # monthly
                key = Function("DATE_FORMAT", Ticket.creation, "%b %Y")
                sort = Function("DATE_FORMAT", Ticket.creation, "%Y%m")
            q = (
                frappe.qb.from_(Ticket)
                .select(key.as_("date"), Count(Ticket.name).as_("count"))
                .groupby(sort)
                .orderby(sort)
            )
        else:
            q = frappe.qb.from_(Ticket).select(Count(Ticket.name).as_("count"))

        q = (
            q.where(Ticket.creation >= from_date)
            .where(Ticket.creation < to_date_plus_one)
            .where(Ticket.agreement_status == "Failed")
        )
        q = _apply_scope(q, Ticket, scope, value)
        return q.run(as_dict=True)

    current_rows = _query(current_from, current_to, grouped=True)
    current_total = sum(row["count"] for row in current_rows)
    previous_total = (_query(previous_from, previous_to) or [{"count": 0}])[0]["count"]

    # Build filled series with 0s for missing buckets
    now = datetime.now()
    if bucket == "daily":
        data = _fill_date_series(current_from, current_to, current_rows)
    elif bucket == "weekly":
        # Build ~4 week buckets: label "Mar 2 – Mar 8"
        week_dict: dict[str, dict] = {}
        cur = date.fromisoformat(str(current_from))
        end = date.fromisoformat(str(current_to))
        # Align to Monday of the first week
        cur -= timedelta(days=cur.weekday())
        while cur <= end:
            iso = cur.strftime("%G-%V")  # matches %x-%v from MySQL
            label = f"{cur.strftime('%b %-d')} – {(cur + timedelta(days=6)).strftime('%b %-d')}"
            week_dict[iso] = {"label": label, "count": 0}
            cur += timedelta(weeks=1)
        for row in current_rows:
            key = str(row["date"])
            if key in week_dict:
                week_dict[key]["count"] = row["count"]
        data = [{"date": v["label"], "count": v["count"]} for v in week_dict.values()]
    else:  # monthly
        num_months = days // 30
        month_dict: dict[str, int] = {}
        for i in range(num_months - 1, -1, -1):
            m = now - relativedelta(months=i)
            month_dict[m.strftime("%b %Y")] = 0
        for row in current_rows:
            key = str(row["date"])
            if key in month_dict:
                month_dict[key] = row["count"]
        data = [{"date": label, "count": count} for label, count in month_dict.items()]

    return {
        "data": data,
        "total": current_total,
        "percentage_change": calculate_percentage_change(current_total, previous_total),
    }


@frappe.whitelist()
@agent_only
def get_avg_first_response_time(
    dt: str,
    dn: str,
    period: str = "last month",
) -> dict:
    return get_avg_time_metric(period, "first_response_time", _resolve_scope(dt), dn)


@frappe.whitelist()
@agent_only
def get_avg_resolution_time(
    dt: str,
    dn: str,
    period: str = "last month",
) -> dict:
    return get_avg_time_metric(period, "resolution_time", _resolve_scope(dt), dn)


@frappe.whitelist()
@agent_only
def get_ticket_stats(
    dt: str,
    dn: str,
    period: str = "last month",
) -> dict:
    scope = _resolve_scope(dt)

    return {
        # "total_tickets": _get_total_tickets(scope, dn, period),
        "feedback_received": _get_feedback_received(scope, dn, period),
        "sla_violations": _get_sla_violations(scope, dn, period),
        "avg_first_response_time": get_avg_time_metric(
            period, "first_response_time", scope, dn
        ),
        "avg_resolution_time": get_avg_time_metric(
            period, "resolution_time", scope, dn
        ),
    }
