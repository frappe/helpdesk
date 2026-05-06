import json
from datetime import date, timedelta

import frappe
from dateutil.relativedelta import relativedelta
from frappe.query_builder import DocType
from frappe.query_builder.functions import Avg, Count, Function
from frappe.utils import add_months, today
from pypika import Case

from helpdesk.api.agent_home.utils import (
    calculate_percentage_change,
    get_default_agent_dashboard,
    get_ticket_count,
)
from helpdesk.utils import agent_only, format_time_difference


@frappe.whitelist()
@agent_only
def get_dashboard(reset_layout: bool = False):
    dashboard = frappe.db.exists("HD Field Layout", {"user": frappe.session.user})
    dashboard_id = None

    if not dashboard:
        layout = json.loads(get_default_agent_dashboard())
    else:
        dashboard = frappe.db.get_value(
            "HD Field Layout",
            {"user": frappe.session.user},
            ["name", "layout"],
        )
        if reset_layout:
            layout = json.loads(get_default_agent_dashboard())
        else:
            layout = json.loads(dashboard[1])
        dashboard_id = dashboard[0]

    for chart in layout:
        method_name = f"get_{chart['chart']}"
        if hasattr(frappe.get_attr("helpdesk.api.agent_home.agent_home"), method_name):
            method = getattr(
                frappe.get_attr("helpdesk.api.agent_home.agent_home"), method_name
            )
            chart["data"] = method()
        else:
            chart["data"] = None

    return {
        "layout": layout,
        "default_layout": get_default_agent_dashboard(),
        "dashboard_id": dashboard_id,
    }


@frappe.whitelist()
@agent_only
def get_agent_tickets(period: str = "last month"):
    current_from, current_to, previous_from, previous_to = _resolve_window(period)

    def get_ticket_data(from_date, to_date):
        Ticket = DocType("HD Ticket")
        creation_date = Function("DATE", Ticket.creation)
        to_date_plus_one = Function(
            "DATE_ADD", to_date, frappe.qb.terms.PseudoColumn("INTERVAL 1 DAY")
        )

        result = (
            frappe.qb.from_(Ticket)
            .select(
                creation_date.as_("date"),
                Count(Ticket.name).as_("count"),
            )
            .where(Ticket.creation >= from_date)
            .where(Ticket.creation < to_date_plus_one)
            .where(
                Function(
                    "JSON_SEARCH", Ticket._assign, "one", frappe.session.user
                ).isnotnull()
            )
            .groupby(creation_date)
            .orderby(creation_date)
            .run(as_dict=True)
        )
        return result

    current_result = get_ticket_data(current_from, current_to)
    previous_result = get_ticket_data(previous_from, previous_to)

    current_total = sum(row["count"] for row in current_result)
    previous_total = sum(row["count"] for row in previous_result)

    percentage_change = calculate_percentage_change(current_total, previous_total)

    # Fill missing days with 0
    from_date_obj = date.fromisoformat(current_from)
    to_date_obj = date.fromisoformat(current_to)
    date_dict = {}
    current_date = from_date_obj
    while current_date <= to_date_obj:
        date_str = current_date.isoformat()
        date_dict[date_str] = 0
        current_date += timedelta(days=1)

    for row in current_result:
        date_dict[str(row["date"])] = row["count"]

    data = [{"date": date, "count": count} for date, count in sorted(date_dict.items())]

    return {
        "data": data,
        "total": current_total,
        "percentage_change": percentage_change,
    }


def get_avg_time(from_date, to_date, value_expr, extra_cond, group_by_date=False):
    Ticket = DocType("HD Ticket")
    to_date_plus_one = Function(
        "DATE_ADD", to_date, frappe.qb.terms.PseudoColumn("INTERVAL 1 DAY")
    )

    query = frappe.qb.from_(Ticket)

    if group_by_date:
        creation_date = Function("DATE", Ticket.creation)
        query = (
            query.select(
                creation_date.as_("date"),
                Avg(value_expr).as_("avg_time"),
            )
            .groupby(creation_date)
            .orderby(creation_date)
        )
    else:
        query = query.select(Avg(value_expr).as_("avg_time"))

    query = (
        query.where(Ticket.creation >= from_date)
        .where(Ticket.creation < to_date_plus_one)
        .where(
            Function(
                "JSON_SEARCH", Ticket._assign, "one", frappe.session.user
            ).isnotnull()
        )
    )
    if extra_cond is not None:
        query = query.where(extra_cond)

    result = query.run(as_dict=True)

    if group_by_date:
        return result

    return result[0]["avg_time"] if result and result[0]["avg_time"] is not None else 0


def _resolve_window(period: str):
    """Returns (current_from, current_to, prev_from, prev_to) using a rolling
    window via date_diff (matches dashboard.py)."""
    periods = {
        "last 7 days": 7,
        "last week": 7,
        "last month": 30,
        "last 3 months": 90,
    }
    days = periods.get((period or "").lower(), 30)

    current_to = frappe.utils.nowdate()
    current_from = frappe.utils.add_days(current_to, -(days - 1))

    diff = frappe.utils.date_diff(current_to, current_from)
    if diff == 0:
        diff = 1
    previous_from = frappe.utils.add_days(current_from, -diff)
    previous_to = frappe.utils.add_days(current_from, -1)

    return current_from, current_to, previous_from, previous_to


def _get_avg_time_metric(period: str, value_expr, extra_cond) -> dict:
    current_from, current_to, previous_from, previous_to = _resolve_window(period)

    current_result = get_avg_time(
        current_from, current_to, value_expr, extra_cond, group_by_date=True
    )

    current_avg = get_avg_time(current_from, current_to, value_expr, extra_cond)
    previous_avg = get_avg_time(previous_from, previous_to, value_expr, extra_cond)

    percentage_change = calculate_percentage_change(current_avg, previous_avg)

    # Fill missing days with 0
    from_date_obj = date.fromisoformat(current_from)
    to_date_obj = date.fromisoformat(current_to)
    date_dict = {}
    current_date = from_date_obj
    while current_date <= to_date_obj:
        date_str = current_date.isoformat()
        date_dict[date_str] = 0
        current_date += timedelta(days=1)

    for row in current_result:
        date_dict[str(row["date"])] = round(row["avg_time"] or 0, 2)

    data = [
        {"date": date, "avg_time": avg_time}
        for date, avg_time in sorted(date_dict.items())
    ]

    return {
        "data": data,
        "average": round(current_avg, 2),
        "percentage_change": percentage_change,
    }


@frappe.whitelist()
@agent_only
def get_avg_first_response_time(period: str = "last month"):
    Ticket = DocType("HD Ticket")
    return _get_avg_time_metric(
        period,
        value_expr=Ticket.first_response_time,
        extra_cond=Ticket.first_responded_on.isnotnull(),
    )


@frappe.whitelist()
@agent_only
def get_avg_resolution_time(period: str = "last month"):
    Ticket = DocType("HD Ticket")
    resolved_statuses = frappe.get_all(
        "HD Ticket Status",
        filters={"category": "Resolved"},
        pluck="name",
    )
    extra_cond = Ticket.status.isin(resolved_statuses) if resolved_statuses else None
    return _get_avg_time_metric(
        period,
        value_expr=Ticket.resolution_time,
        extra_cond=extra_cond,
    )


@frappe.whitelist()
@agent_only
def get_recent_feedback(
    period: str = "all_time",
    sort_order: str = "positive_first",
    from_date: str = None,
    to_date: str = None,
):
    agent = frappe.session.user
    Ticket = DocType("HD Ticket")
    Contact = DocType("Contact")

    # Build period filter
    period_filter = None
    period_end_filter = None
    if period == "custom_range" and from_date and to_date:
        period_filter = from_date
        period_end_filter = to_date
    elif period == "last_week":
        period_filter = frappe.utils.add_days(frappe.utils.nowdate(), -7)
    elif period == "last_month":
        period_filter = frappe.utils.add_days(frappe.utils.nowdate(), -30)
    elif period == "last_3_months":
        period_filter = frappe.utils.add_days(frappe.utils.nowdate(), -90)

    # Base query conditions
    base_conditions = [
        Ticket.feedback_rating > 0,
        Function("JSON_SEARCH", Ticket._assign, "one", agent).isnotnull(),
    ]
    if period_filter:
        base_conditions.append(Ticket.creation >= period_filter)
    if period_end_filter:
        to_date_plus_one = Function(
            "DATE_ADD",
            period_end_filter,
            frappe.qb.terms.PseudoColumn("INTERVAL 1 DAY"),
        )
        base_conditions.append(Ticket.creation < to_date_plus_one)

    # Get average rating and total feedbacks
    avg_query = frappe.qb.from_(Ticket).select(
        (Avg(Ticket.feedback_rating) * 5).as_("average"),
        Count(Ticket.name).as_("total_feedbacks"),
    )
    for condition in base_conditions:
        avg_query = avg_query.where(condition)
    avg_result = avg_query.run(as_dict=True)

    average_rating = (
        avg_result[0]["average"]
        if avg_result and avg_result[0]["average"] is not None
        else 0
    )
    total_feedbacks = (
        avg_result[0]["total_feedbacks"]
        if avg_result and avg_result[0]["total_feedbacks"] is not None
        else 0
    )

    # Get rating distribution (1-5 stars)
    rating_dist_query = (
        frappe.qb.from_(Ticket)
        .select(
            Function("ROUND", Ticket.feedback_rating * 5).as_("star_rating"),
            Count(Ticket.name).as_("count"),
        )
        .groupby(Function("ROUND", Ticket.feedback_rating * 5))
    )
    for condition in base_conditions:
        rating_dist_query = rating_dist_query.where(condition)
    rating_dist_result = rating_dist_query.run(as_dict=True)

    # Build rating distribution dict
    rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for row in rating_dist_result:
        star = int(row["star_rating"])
        if 1 <= star <= 5:
            rating_distribution[star] = row["count"]

    # Determine sort order
    if sort_order == "negative_first":
        order_direction = frappe.qb.asc
    else:
        order_direction = frappe.qb.desc

    # Get recent feedbacks
    feedback_query = (
        frappe.qb.from_(Ticket)
        .left_join(Contact)
        .on(Ticket.contact == Contact.name)
        .select(
            Ticket.name,
            Ticket.subject,
            Ticket.feedback_rating,
            Ticket.feedback,
            Ticket.feedback_extra,
            Ticket.contact,
            Ticket.modified,
            Contact.full_name.as_("contact_name"),
            Contact.image.as_("contact_image"),
        )
        .orderby(Ticket.feedback_rating, order=order_direction)
        .orderby(Ticket.modified, order=frappe.qb.desc)
        .limit(20)
    )
    for condition in base_conditions:
        feedback_query = feedback_query.where(condition)
    feedback = feedback_query.run(as_dict=True)

    # Add star rating to each feedback
    for f in feedback:
        f["star_rating"] = round(f["feedback_rating"] * 5, 1)

    return {
        "average_rating": round(average_rating, 1),
        "total_feedbacks": total_feedbacks,
        "rating_distribution": rating_distribution,
        "recent_feedbacks": feedback,
    }


@frappe.whitelist()
@agent_only
def get_avg_time_metrics(
    period: str = "6m", from_date: str = None, to_date: str = None
):
    periods = {
        "3m": 90,
        "6m": 180,
        "1y": 365,
    }

    agent = frappe.session.user

    if period == "custom_range" and from_date and to_date:
        current_from = from_date
        current_to = to_date
    else:
        days = periods.get(period, 180)
        current_from = frappe.utils.add_days(frappe.utils.nowdate(), -days)
        current_to = frappe.utils.nowdate()

    Ticket = DocType("HD Ticket")
    to_date_plus_one = Function(
        "DATE_ADD", current_to, frappe.qb.terms.PseudoColumn("INTERVAL 1 DAY")
    )

    resolved_statuses = frappe.get_all(
        "HD Ticket Status",
        filters={"category": "Resolved"},
        pluck="name",
    )

    # Monthly aggregation query using query builder. Per-series gating mirrors
    # dashboard.py: first-response avg requires first_responded_on; resolution
    # avg requires status IN resolved_statuses.
    month_abbr = Function("DATE_FORMAT", Ticket.creation, "%b")
    year_val = Function("YEAR", Ticket.creation)
    month_val = Function("MONTH", Ticket.creation)

    first_response_value = (
        Case()
        .when(Ticket.first_responded_on.isnotnull(), Ticket.first_response_time)
        .else_(None)
    )
    resolution_gate = (
        Ticket.status.isin(resolved_statuses) if resolved_statuses else None
    )
    resolution_value = (
        Case().when(resolution_gate, Ticket.resolution_time).else_(None)
        if resolution_gate is not None
        else Ticket.resolution_time
    )

    result = (
        frappe.qb.from_(Ticket)
        .select(
            month_abbr.as_("month"),
            year_val.as_("year"),
            month_val.as_("month_num"),
            Avg(first_response_value).as_("avg_first_response"),
            Avg(resolution_value).as_("avg_resolution"),
        )
        .where(Ticket.creation >= current_from)
        .where(Ticket.creation < to_date_plus_one)
        .where(Function("JSON_SEARCH", Ticket._assign, "one", agent).isnotnull())
        .groupby(year_val, month_val)
        .orderby(year_val)
        .orderby(month_val)
        .run(as_dict=True)
    )

    data_dict = {}
    for row in result:
        key = f"{row['year']}-{row['month_num']:02d}"
        data_dict[key] = {
            "month": row["month"],
            "avg_first": round(row["avg_first_response"] or 0),
            "avg_resolution": round(row["avg_resolution"] or 0),
        }

    current_to_date = frappe.utils.get_datetime(current_to)
    current_from_date = frappe.utils.get_datetime(current_from)

    num_months = (
        (current_to_date.year - current_from_date.year) * 12
        + (current_to_date.month - current_from_date.month)
        + 1
    )

    data = []
    for i in range(num_months - 1, -1, -1):
        month_date = current_to_date - relativedelta(months=i)
        key = f"{month_date.year}-{month_date.month:02d}"
        if key in data_dict:
            data.append(
                [
                    data_dict[key]["month"],
                    data_dict[key]["avg_first"],
                    data_dict[key]["avg_resolution"],
                ]
            )
        else:
            data.append(
                [
                    month_date.strftime("%b"),
                    0,
                    0,
                ]
            )

    # Calculate overall averages for the period using query builder, with the
    # same per-series gating as the monthly aggregation above.
    overall_result = (
        frappe.qb.from_(Ticket)
        .select(
            Avg(first_response_value).as_("avg_first_response"),
            Avg(resolution_value).as_("avg_resolution"),
        )
        .where(Ticket.creation >= current_from)
        .where(Ticket.creation < to_date_plus_one)
        .where(Function("JSON_SEARCH", Ticket._assign, "one", agent).isnotnull())
        .run(as_dict=True)
    )

    overall_avg_first = (
        overall_result[0]["avg_first_response"]
        if overall_result and overall_result[0]["avg_first_response"] is not None
        else 0
    )
    overall_avg_resolution = (
        overall_result[0]["avg_resolution"]
        if overall_result and overall_result[0]["avg_resolution"] is not None
        else 0
    )

    return {
        "data": data,
        "averages": {
            "first_response": overall_avg_first,
            "resolution": overall_avg_resolution,
        },
    }


def _get_priority_range():
    priorities = frappe.get_all(
        "HD Ticket Priority", fields="integer_value", filters={"disabled": 0}
    )
    if priorities:
        min_priority = min(priorities, key=lambda x: x["integer_value"])[
            "integer_value"
        ]
        max_priority = max(priorities, key=lambda x: x["integer_value"])[
            "integer_value"
        ]
    else:
        min_priority = max_priority = 0
    return min_priority, max_priority


def _get_upcoming_sla_tickets(limit=10):
    filters = [
        ["sla", "is", "set"],
        ["agreement_status", "in", ["First Response Due", "Resolution Due"]],
        ["status_category", "=", "Open"],
        ["_assign", "like", f"%{frappe.session.user}%"],
        ["creation", "between", [add_months(today(), -6), today()]],
    ]

    tickets = frappe.get_list(
        "HD Ticket",
        fields=[
            "name",
            "subject",
            "status",
            "priority",
            "priority.integer_value as priority_integer_value",
            "agent_group",
            "response_by",
            "resolution_by",
            "agreement_status",
            "creation",
        ],
        filters=filters,
        order_by="response_by asc",
        limit=limit,
    )

    for ticket in tickets:
        agreement_status = ticket.get("agreement_status", "")
        if agreement_status == "Resolution Due":
            due_time = ticket.get("resolution_by")
            time_until = format_time_difference(due_time, context="until")
            reason_text = (
                f"Resolution due in {time_until}"
                if time_until != "overdue"
                else "Resolution overdue"
            )
        else:
            due_time = ticket.get("response_by")
            time_until = format_time_difference(due_time, context="until")
            reason_text = (
                f"Response due in {time_until}"
                if time_until != "overdue"
                else "Response overdue"
            )

        # Calculate seconds until due for frontend urgency coloring
        seconds_until_due = None
        if due_time:
            now = frappe.utils.now_datetime()
            if isinstance(due_time, str):
                due_time = frappe.utils.get_datetime(due_time)
            seconds_until_due = (due_time - now).total_seconds()

        ticket["reason"] = {
            "type": "upcoming_sla",
            "text": reason_text,
            "seconds_until_due": seconds_until_due,
        }

    total_count = get_ticket_count(filters)

    return tickets, total_count


def _get_new_tickets(limit=10):
    one_week_ago = frappe.utils.add_to_date(frappe.utils.now_datetime(), days=-7)

    ToDo = DocType("ToDo")
    assigned_tickets = (
        frappe.qb.from_(ToDo)
        .select(ToDo.reference_name)
        .distinct()
        .where(ToDo.reference_type == "HD Ticket")
        .where(ToDo.allocated_to == frappe.session.user)
        .where(ToDo.creation >= one_week_ago)
        .where(ToDo.status == "Open")
        .run(as_dict=False)
    )
    ticket_names = [row[0] for row in assigned_tickets]

    if not ticket_names:
        return [], 0

    filters = [
        ["name", "in", ticket_names],
        ["_assign", "like", f"%{frappe.session.user}%"],
        ["status_category", "=", "Open"],
        ["creation", "between", [add_months(today(), -6), today()]],
    ]

    tickets = frappe.get_list(
        "HD Ticket",
        fields=[
            "name",
            "subject",
            "status",
            "priority",
            "priority.integer_value as priority_integer_value",
            "agent_group",
            "creation",
        ],
        filters=filters,
        order_by="creation desc",
        limit=limit,
    )

    for ticket in tickets:
        ticket["reason"] = {
            "type": "new_tickets",
            "text": "Recently assigned",
        }

    total_count = get_ticket_count(filters=filters)

    return tickets, total_count


def _get_pending_response_tickets(limit=10):
    filters = [
        ["_assign", "like", f"%{frappe.session.user}%"],
        ["status_category", "=", "Open"],
        ["last_customer_response", "is", "set"],
        ["creation", "between", [add_months(today(), -6), today()]],
    ]

    tickets = frappe.get_list(
        "HD Ticket",
        fields=[
            "name",
            "subject",
            "status",
            "priority",
            "priority.integer_value as priority_integer_value",
            "agent_group",
            "creation",
            "last_customer_response",
        ],
        filters=filters,
        order_by="last_customer_response asc",
        limit=limit,
    )

    total_count = get_ticket_count(filters)

    for t in tickets:
        time_ago = format_time_difference(t.get("last_customer_response"))
        t["reason"] = {
            "type": "pending",
            "text": f"Pending for {time_ago}",
        }

    return tickets, total_count


@frappe.whitelist()
@agent_only
def get_pending_tickets(ticket_type: str = "upcoming_sla"):
    min_priority, max_priority = _get_priority_range()

    if ticket_type == "upcoming_sla":
        tickets, total_count = _get_upcoming_sla_tickets(limit=6)
    elif ticket_type == "new_tickets":
        tickets, total_count = _get_new_tickets(limit=6)
    elif ticket_type == "pending":
        tickets, total_count = _get_pending_response_tickets(limit=6)

    return {
        "tickets": tickets,
        "total_pending_tickets": total_count,
        "min_priority": min_priority,
        "max_priority": max_priority,
    }
