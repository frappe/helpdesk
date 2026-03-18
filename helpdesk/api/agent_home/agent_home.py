import json
from datetime import date, datetime, timedelta

import frappe
from dateutil.relativedelta import relativedelta
from frappe.query_builder import DocType
from frappe.query_builder.functions import Avg, Count, Function

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
    periods = {"last week": 7, "last month": 30, "last 3 months": 90}
    days = periods.get(period, 7)

    current_from = frappe.utils.add_days(frappe.utils.nowdate(), -(days - 1))
    current_to = frappe.utils.nowdate()
    previous_from = frappe.utils.add_days(frappe.utils.nowdate(), -(2 * days - 1))
    previous_to = frappe.utils.add_days(frappe.utils.nowdate(), -days)

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


def get_avg_time(from_date, to_date, time_field, group_by_date=False):
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
                Avg(Ticket[time_field]).as_("avg_time"),
            )
            .groupby(creation_date)
            .orderby(creation_date)
        )
    else:
        query = query.select(Avg(Ticket[time_field]).as_("avg_time"))

    result = (
        query.where(Ticket.creation >= from_date)
        .where(Ticket.creation < to_date_plus_one)
        .where(
            Function(
                "JSON_SEARCH", Ticket._assign, "one", frappe.session.user
            ).isnotnull()
        )
        .where(Ticket[time_field].isnotnull())
        .run(as_dict=True)
    )

    if group_by_date:
        return result

    return result[0]["avg_time"] if result and result[0]["avg_time"] is not None else 0


def _get_avg_time_metric(period: str, time_field: str) -> dict:
    periods = {"last week": 7, "last month": 30, "last 3 months": 90}
    days = periods.get(period, 7)

    current_from = frappe.utils.add_days(frappe.utils.nowdate(), -(days - 1))
    current_to = frappe.utils.nowdate()
    previous_from = frappe.utils.add_days(frappe.utils.nowdate(), -(2 * days - 1))
    previous_to = frappe.utils.add_days(frappe.utils.nowdate(), -days)

    current_result = get_avg_time(
        current_from, current_to, time_field, group_by_date=True
    )

    current_avg = get_avg_time(current_from, current_to, time_field)
    previous_avg = get_avg_time(previous_from, previous_to, time_field)

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
    return _get_avg_time_metric(period, "first_response_time")


@frappe.whitelist()
@agent_only
def get_avg_resolution_time(period: str = "last month"):
    return _get_avg_time_metric(period, "resolution_time")


@frappe.whitelist()
@agent_only
def get_recent_feedback(period: str = "all_time", sort_order: str = "positive_first"):
    agent = frappe.session.user
    Ticket = DocType("HD Ticket")
    Contact = DocType("Contact")

    # Build period filter
    period_filter = None
    if period == "last_week":
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
        base_conditions.append(Ticket.modified >= period_filter)

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
def get_avg_time_metrics(period: str = "6m"):
    periods = {
        "3m": 90,
        "6m": 180,
        "1y": 365,
    }

    days = periods.get(period, 180)
    agent = frappe.session.user

    current_from = frappe.utils.add_days(frappe.utils.nowdate(), -days)
    current_to = frappe.utils.nowdate()

    Ticket = DocType("HD Ticket")
    to_date_plus_one = Function(
        "DATE_ADD", current_to, frappe.qb.terms.PseudoColumn("INTERVAL 1 DAY")
    )

    # Monthly aggregation query using query builder
    month_abbr = Function("DATE_FORMAT", Ticket.creation, "%b")
    year_val = Function("YEAR", Ticket.creation)
    month_val = Function("MONTH", Ticket.creation)

    result = (
        frappe.qb.from_(Ticket)
        .select(
            month_abbr.as_("month"),
            year_val.as_("year"),
            month_val.as_("month_num"),
            Avg(Ticket.first_response_time).as_("avg_first_response"),
            Avg(Ticket.resolution_time).as_("avg_resolution"),
        )
        .where(Ticket.creation >= current_from)
        .where(Ticket.creation < to_date_plus_one)
        .where(Function("JSON_SEARCH", Ticket._assign, "one", agent).isnotnull())
        .where(
            Ticket.first_response_time.isnotnull() | Ticket.resolution_time.isnotnull()
        )
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

    now = datetime.now()
    num_months = days // 30
    data = []
    for i in range(num_months - 1, -1, -1):
        month_date = now - relativedelta(months=i)
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

    # Calculate overall averages for the period using query builder
    overall_result = (
        frappe.qb.from_(Ticket)
        .select(
            Avg(Ticket.first_response_time).as_("avg_first_response"),
            Avg(Ticket.resolution_time).as_("avg_resolution"),
        )
        .where(Ticket.creation >= current_from)
        .where(Ticket.creation < to_date_plus_one)
        .where(Function("JSON_SEARCH", Ticket._assign, "one", agent).isnotnull())
        .where(
            Ticket.first_response_time.isnotnull() | Ticket.resolution_time.isnotnull()
        )
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
    priorities = frappe.get_all("HD Ticket Priority", fields="integer_value")
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
        ["sla", "!=", ""],
        ["agreement_status", "in", ["First Response Due", "Resolution Due"]],
        ["status_category", "!=", "Resolved"],
        ["_assign", "like", f"%{frappe.session.user}%"],
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
    one_day_ago = frappe.utils.add_to_date(frappe.utils.now_datetime(), hours=-24)

    ToDo = DocType("ToDo")
    assigned_tickets = (
        frappe.qb.from_(ToDo)
        .select(ToDo.reference_name)
        .distinct()
        .where(ToDo.reference_type == "HD Ticket")
        .where(ToDo.allocated_to == frappe.session.user)
        .where(ToDo.creation >= one_day_ago)
        .where(ToDo.status == "Open")
        .run(as_dict=False)
    )
    ticket_names = [row[0] for row in assigned_tickets]

    if not ticket_names:
        return [], 0

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
        filters=[
            ["name", "in", ticket_names],
            ["_assign", "like", f"%{frappe.session.user}%"],
            ["status_category", "=", "Open"],
        ],
        order_by="creation desc",
        limit=limit,
    )

    for ticket in tickets:
        ticket["reason"] = {
            "type": "new_tickets",
            "text": "Recently assigned",
        }

    total_count = get_ticket_count(
        filters=[
            ["name", "in", ticket_names],
            ["_assign", "like", f"%{frappe.session.user}%"],
            ["status_category", "=", "Open"],
        ]
    )

    return tickets, total_count


def _get_pending_response_tickets(limit=10):
    filters = [
        ["_assign", "like", f"%{frappe.session.user}%"],
        ["status_category", "!=", "Resolved"],
        ["last_customer_response", "is", "set"],
        ["last_agent_response", "is", "not set"],
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
