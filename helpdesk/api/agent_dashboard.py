import json
from datetime import date, timedelta

import frappe

from helpdesk.utils import agent_only


def get_default_agent_dashboard():
    return '[{"chart":"recently_assigned_tickets","layout":{"x":17,"y":25,"w":17,"h":27,"i":"0.5901090349104408","minW":16,"minH":27,"maxH":27,"moved":false}},{"chart":"recent_feedback","layout":{"x":34,"y":25,"w":16,"h":27,"i":"0.2090867593567277","minW":16,"minH":27,"maxW":27,"maxH":27,"moved":false}},{"chart":"avg_time_metrics","layout":{"x":0,"y":0,"w":50,"h":25,"i":"0.9444757118289221","moved":false,"minW":18,"minH":24,"maxH":44}},{"chart":"upcoming_sla_violations","layout":{"x":0,"y":52,"w":50,"h":25,"i":"0.644411970698438","moved":false,"minW":25,"minH":25,"maxH":25}},{"chart":"pending_tickets","layout":{"x":0,"y":77,"w":50,"h":24,"i":"0.12878740671098265","moved":false,"minW":25,"minH":24,"maxH":24}},{"chart":"avg_resolution_time","layout":{"x":0,"y":43,"w":17,"h":9,"i":"0.17044916608149618","moved":false,"minW":14,"minH":9,"maxH":9}},{"chart":"avg_first_response_time","layout":{"x":0,"y":34,"w":17,"h":9,"i":"0.408504238844829","moved":false,"minW":14,"minH":9,"maxH":9}},{"chart":"agent_tickets","layout":{"x":0,"y":25,"w":17,"h":9,"i":"0.38621973888392136","moved":false,"minW":14,"minH":9,"maxH":9}}]'


@frappe.whitelist()
@agent_only
def get_dashboard(reset_layout=False):
    dashboard = frappe.db.exists("HD Field Layout", {"user": frappe.session.user})

    if not dashboard:
        dashboard = frappe.get_doc(
            {
                "doctype": "HD Field Layout",
                "user": frappe.session.user,
                "type": "Landing Page",
                "layout": get_default_agent_dashboard(),
            },
        ).insert(ignore_permissions=True)
        frappe.db.commit()  # nosemgrep
        layout = json.loads(get_default_agent_dashboard())
    else:
        dashboard = frappe.get_doc(
            "HD Field Layout",
            {"user": frappe.session.user},
            fields=["name", "layout"],
        )
        if reset_layout:
            layout = json.loads(get_default_agent_dashboard())
        else:
            layout = json.loads(dashboard.layout)

    for chart in layout:
        method_name = f"get_{chart['chart']}"
        if hasattr(frappe.get_attr("helpdesk.api.agent_dashboard"), method_name):
            method = getattr(
                frappe.get_attr("helpdesk.api.agent_dashboard"), method_name
            )
            chart["data"] = method()
        else:
            chart["data"] = None

    return {
        "layout": layout,
        "default_layout": get_default_agent_dashboard(),
        "dashboard_id": dashboard.name,
    }


@frappe.whitelist()
@agent_only
def get_agent_tickets(period="last month"):
    periods = {"last week": 7, "last month": 30, "last 3 months": 90}
    days = periods.get(period, 7)

    current_from = frappe.utils.add_days(frappe.utils.nowdate(), -days)
    current_to = frappe.utils.nowdate()
    previous_from = frappe.utils.add_days(frappe.utils.nowdate(), -2 * days)
    previous_to = frappe.utils.add_days(frappe.utils.nowdate(), -days)

    def get_ticket_data(from_date, to_date):
        result = frappe.db.sql(
            """
            SELECT
                DATE(creation) as date,
                COUNT(name) as count
            FROM `tabHD Ticket`
            WHERE creation >= %(from_date)s AND creation < DATE_ADD(%(to_date)s, INTERVAL 1 DAY)
            AND JSON_SEARCH(_assign, 'one', %(agent)s) IS NOT NULL
            GROUP BY DATE(creation)
            ORDER BY DATE(creation)
            """,
            {
                "from_date": from_date,
                "to_date": to_date,
                "agent": frappe.session.user,
            },
            as_dict=1,
        )
        return result

    current_result = get_ticket_data(current_from, current_to)
    previous_result = get_ticket_data(previous_from, previous_to)

    current_total = sum(row["count"] for row in current_result)
    previous_total = sum(row["count"] for row in previous_result)

    if previous_total > 0:
        percentage_change = round(
            ((current_total - previous_total) / previous_total) * 100, 2
        )
    elif current_total > 0:
        percentage_change = 999
    else:
        percentage_change = 0

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


def get_avg_time(from_date, to_date, time_field):
    result = frappe.db.sql(
        f"""
        SELECT AVG({time_field}) as avg_time
        FROM `tabHD Ticket` # noqa: W604
        WHERE creation >= %(from_date)s AND creation < DATE_ADD(%(to_date)s, INTERVAL 1 DAY)
        AND JSON_SEARCH(_assign, 'one', %(agent)s) IS NOT NULL
        AND {time_field} IS NOT NULL
        """,
        {
            "from_date": from_date,
            "to_date": to_date,
            "agent": frappe.session.user,
        },
        as_dict=1,
    )
    return result[0]["avg_time"] if result and result[0]["avg_time"] is not None else 0


@frappe.whitelist()
@agent_only
def get_avg_first_response_time(period="last month"):
    periods = {"last week": 7, "last month": 30, "last 3 months": 90}
    days = periods.get(period, 7)

    current_from = frappe.utils.add_days(frappe.utils.nowdate(), -days)
    current_to = frappe.utils.nowdate()
    previous_from = frappe.utils.add_days(frappe.utils.nowdate(), -2 * days)
    previous_to = frappe.utils.add_days(frappe.utils.nowdate(), -days)

    def get_avg_time_data(from_date, to_date):
        result = frappe.db.sql(
            """
            SELECT
                DATE(creation) as date,
                AVG(first_response_time) as avg_time
            FROM `tabHD Ticket` # noqa: W604
            WHERE creation >= %(from_date)s AND creation < DATE_ADD(%(to_date)s, INTERVAL 1 DAY)
            AND JSON_SEARCH(_assign, 'one', %(agent)s) IS NOT NULL
            AND first_response_time IS NOT NULL
            GROUP BY DATE(creation)
            ORDER BY DATE(creation)
            """,
            {
                "from_date": from_date,
                "to_date": to_date,
                "agent": frappe.session.user,
            },
            as_dict=1,
        )
        return result

    current_result = get_avg_time_data(current_from, current_to)

    current_avg = get_avg_time(current_from, current_to, "first_response_time")
    previous_avg = get_avg_time(previous_from, previous_to, "first_response_time")

    if previous_avg > 0:
        percentage_change = round(
            ((current_avg - previous_avg) / previous_avg) * 100, 2
        )
    elif current_avg > 0:
        percentage_change = 999
    else:
        percentage_change = 0

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
def get_avg_resolution_time(period="last month"):
    periods = {"last week": 7, "last month": 30, "last 3 months": 90}
    days = periods.get(period, 7)

    current_from = frappe.utils.add_days(frappe.utils.nowdate(), -days)
    current_to = frappe.utils.nowdate()
    previous_from = frappe.utils.add_days(frappe.utils.nowdate(), -2 * days)
    previous_to = frappe.utils.add_days(frappe.utils.nowdate(), -days)

    def get_avg_time_data(from_date, to_date):
        result = frappe.db.sql(
            """
            SELECT
                DATE(creation) as date,
                AVG(resolution_time) as avg_time
            FROM `tabHD Ticket` # noqa: W604
            WHERE creation >= %(from_date)s AND creation < DATE_ADD(%(to_date)s, INTERVAL 1 DAY)
            AND JSON_SEARCH(_assign, 'one', %(agent)s) IS NOT NULL
            AND resolution_time IS NOT NULL
            GROUP BY DATE(creation)
            ORDER BY DATE(creation)
            """,
            {
                "from_date": from_date,
                "to_date": to_date,
                "agent": frappe.session.user,
            },
            as_dict=1,
        )
        return result

    current_result = get_avg_time_data(current_from, current_to)

    current_avg = get_avg_time(current_from, current_to, "resolution_time")
    previous_avg = get_avg_time(previous_from, previous_to, "resolution_time")

    if previous_avg > 0:
        percentage_change = round(
            ((current_avg - previous_avg) / previous_avg) * 100, 2
        )
    elif current_avg > 0:
        percentage_change = 999
    else:
        percentage_change = 0

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
def get_sla_fulfilled_count(period="last month"):
    periods = {"last week": 7, "last month": 30, "last 3 months": 90}
    days = periods.get(period, 7)

    current_from = frappe.utils.add_days(frappe.utils.nowdate(), -days)
    current_to = frappe.utils.nowdate()
    previous_from = frappe.utils.add_days(frappe.utils.nowdate(), -2 * days)
    previous_to = frappe.utils.add_days(frappe.utils.nowdate(), -days)

    resolved_statuses = tuple(
        frappe.get_all(
            "HD Ticket Status",
            filters={"category": "Resolved"},
            pluck="name",
        )
    )

    def get_sla_data(from_date, to_date):
        fulfilled_result = frappe.db.sql(
            """
            SELECT COUNT(name) as fulfilled_count
            FROM `tabHD Ticket`
            WHERE creation >= %(from_date)s AND creation < DATE_ADD(%(to_date)s, INTERVAL 1 DAY)
            AND agreement_status = 'Fulfilled'
            AND status in %(resolved_statuses)s
            AND JSON_SEARCH(_assign, 'one', %(agent)s) IS NOT NULL
            """,
            {
                "from_date": from_date,
                "to_date": to_date,
                "resolved_statuses": resolved_statuses,
                "agent": frappe.session.user,
            },
            as_dict=1,
        )

        total_result = frappe.db.sql(
            """
            SELECT COUNT(name) as total_count
            FROM `tabHD Ticket`
            WHERE creation >= %(from_date)s AND creation < DATE_ADD(%(to_date)s, INTERVAL 1 DAY)
            AND status in %(resolved_statuses)s
            AND JSON_SEARCH(_assign, 'one', %(agent)s) IS NOT NULL
            """,
            {
                "from_date": from_date,
                "to_date": to_date,
                "resolved_statuses": resolved_statuses,
                "agent": frappe.session.user,
            },
            as_dict=1,
        )

        fulfilled_count = fulfilled_result[0].fulfilled_count or 0
        total_count = total_result[0].total_count or 0
        percentage = (fulfilled_count / total_count * 100) if total_count > 0 else 0

        return percentage

    current_percentage = get_sla_data(current_from, current_to)
    previous_percentage = get_sla_data(previous_from, previous_to)

    if previous_percentage > 0:
        percentage_change = round(
            ((current_percentage - previous_percentage) / previous_percentage) * 100, 2
        )
    elif current_percentage > 0:
        percentage_change = 999
    else:
        percentage_change = 0

    return {
        "percentage": current_percentage,
        "percentage_change": percentage_change,
    }


@frappe.whitelist()
@agent_only
def get_unresolved_tickets():
    allowed_statuses = frappe.get_all(
        "HD Ticket Status", filters={"category": ["!=", "Resolved"]}, pluck="name"
    )
    count = frappe.db.count(
        "HD Ticket",
        filters=[
            ["_assign", "like", f"%{frappe.session.user}%"],
            ["status", "in", allowed_statuses],
        ],
    )
    return {"total": count}


@frappe.whitelist()
@agent_only
def get_recently_assigned_tickets():
    one_week_ago = frappe.utils.add_days(frappe.utils.nowdate(), -7)
    assigned_tickets = frappe.db.sql(
        """
        SELECT DISTINCT reference_name
        FROM `tabToDo`
        WHERE reference_type = 'HD Ticket'
        AND allocated_to = %(user)s
        AND creation >= %(one_week_ago)s
        """,
        {"user": frappe.session.user, "one_week_ago": one_week_ago},
        as_dict=False,
    )
    ticket_names = [row[0] for row in assigned_tickets]

    if not ticket_names:
        return {"count": 0, "tickets": []}

    allowed_statuses = frappe.get_all(
        "HD Ticket Status", filters={"category": ["!=", "Resolved"]}, pluck="name"
    )

    # Count tickets assigned in past week that are still assigned and not resolved
    count = frappe.db.count(
        "HD Ticket",
        filters=[
            ["name", "in", ticket_names],
            ["_assign", "like", f"%{frappe.session.user}%"],
            ["status", "in", allowed_statuses],
        ],
    )

    tickets = frappe.get_list(
        "HD Ticket",
        fields=[
            "name",
            "subject",
            "status",
            "priority",
            "modified",
            "creation",
        ],
        filters=[
            ["name", "in", ticket_names],
            ["_assign", "like", f"%{frappe.session.user}%"],
            ["status", "in", allowed_statuses],
        ],
        order_by="modified desc",
        limit=5,
    )

    return {"count": count, "tickets": tickets}


@frappe.whitelist()
@agent_only
def get_recent_feedback():
    agent = frappe.session.user

    avg_result = frappe.db.sql(
        """
        SELECT AVG(feedback_rating) * 5 as average
        FROM `tabHD Ticket`
        WHERE feedback_rating > 0
        AND JSON_SEARCH(_assign, 'one', %(agent)s) IS NOT NULL
        """,
        {"agent": agent},
        as_dict=True,
    )
    average_rating = (
        avg_result[0]["average"]
        if avg_result and avg_result[0]["average"] is not None
        else 0
    )

    feedback = frappe.get_list(
        "HD Ticket",
        fields=["name", "feedback_rating", "feedback", "feedback_extra", "contact"],
        filters=[
            ["feedback_rating", ">", 0],
            ["_assign", "like", f"%{agent}%"],
        ],
        order_by="modified desc",
        limit=10,
    )

    return {"average_rating": round(average_rating, 1), "recent_feedbacks": feedback}


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

    result = frappe.db.sql(
        """
        SELECT
            DATE_FORMAT(creation, '%%b') as month,
            YEAR(creation) as year,
            MONTH(creation) as month_num,
            AVG(first_response_time) as avg_first_response,
            AVG(resolution_time) as avg_resolution
        FROM `tabHD Ticket`
        WHERE creation >= %(from_date)s AND creation < DATE_ADD(%(to_date)s, INTERVAL 1 DAY)
        AND JSON_SEARCH(_assign, 'one', %(agent)s) IS NOT NULL
        AND (first_response_time IS NOT NULL OR resolution_time IS NOT NULL)
        GROUP BY YEAR(creation), MONTH(creation)
        ORDER BY YEAR(creation), MONTH(creation)
        """,
        {"from_date": current_from, "to_date": current_to, "agent": agent},
        as_dict=1,
    )

    data_dict = {}
    for row in result:
        key = f"{row['year']}-{row['month_num']:02d}"
        data_dict[key] = {
            "month": row["month"],
            "avg_first": round(row["avg_first_response"] or 0),
            "avg_resolution": round(row["avg_resolution"] or 0),
        }

    # Generate all months in the period
    import datetime

    now = datetime.datetime.now()
    data = []
    for i in range(days // 30 - 1, -1, -1):  # Approximate months from days
        month_date = now - datetime.timedelta(days=30 * i)
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

    # Calculate overall averages for the period
    overall_result = frappe.db.sql(
        """
        SELECT
            AVG(first_response_time) as avg_first_response,
            AVG(resolution_time) as avg_resolution
        FROM `tabHD Ticket`
        WHERE creation >= %(from_date)s AND creation < DATE_ADD(%(to_date)s, INTERVAL 1 DAY)
        AND JSON_SEARCH(_assign, 'one', %(agent)s) IS NOT NULL
        AND (first_response_time IS NOT NULL OR resolution_time IS NOT NULL)
        """,
        {"from_date": current_from, "to_date": current_to, "agent": agent},
        as_dict=1,
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


@frappe.whitelist()
@agent_only
def get_pending_tickets():
    allowed_statuses = frappe.get_all(
        "HD Ticket Status", filters={"category": ["=", "Open"]}, pluck="name"
    )

    # Get all tickets first
    all_tickets = frappe.get_list(
        "HD Ticket",
        fields=[
            "name",
            "subject",
            "status",
            "priority",
            "priority.integer_value",
            "agent_group",
            "response_by",
            "resolution_by",
            "resolution_date",
            "agreement_status",
            "status_category",
            "first_responded_on",
            "creation",
        ],
        filters=[
            ["_assign", "like", f"%{frappe.session.user}%"],
            ["status", "in", allowed_statuses],
        ],
        limit=50,
    )

    ticket_names = [ticket["name"] for ticket in all_tickets]
    if not ticket_names:
        return {
            "tickets": [],
            "min_priority": 0,
            "max_priority": 0,
        }

    # Get last customer reply and last agent reply for each ticket
    last_replies = frappe.db.sql(
        """
        SELECT
            CAST(reference_name AS UNSIGNED) as reference_name_int,
            MAX(CASE WHEN sent_or_received = 'Received' THEN creation END) as last_customer_reply,
            MAX(CASE WHEN sent_or_received = 'Sent' THEN creation END) as last_agent_reply
        FROM `tabCommunication`
        WHERE reference_doctype = 'HD Ticket'
        AND reference_name IN %(ticket_names)s
        GROUP BY reference_name
        """,
        {"ticket_names": ticket_names},
        as_dict=True,
    )

    # Create mappings of ticket name to reply times
    customer_reply_map = {}
    agent_reply_map = {}

    for item in last_replies:
        ticket_id = item["reference_name_int"]
        if ticket_id:
            customer_reply_map[ticket_id] = item["last_customer_reply"]
            agent_reply_map[ticket_id] = item["last_agent_reply"]

    pending_tickets = []
    for ticket in all_tickets:
        ticket_id = ticket["name"]
        last_customer_reply = customer_reply_map.get(ticket_id)
        last_agent_reply = agent_reply_map.get(ticket_id)

        if last_customer_reply and (
            not last_agent_reply or last_agent_reply < last_customer_reply
        ):
            ticket["last_customer_reply"] = last_customer_reply
            ticket["last_agent_reply"] = last_agent_reply
            pending_tickets.append(ticket)

    # Sort pending tickets by last customer reply time (most recent first)
    pending_tickets.sort(key=lambda x: x["last_customer_reply"], reverse=True)

    # Limit to 5 tickets
    tickets = pending_tickets[:5]

    priorities = frappe.get_all("HD Ticket Priority", fields="integer_value")
    min_priority = min(priorities, key=lambda x: x["integer_value"])["integer_value"]
    max_priority = max(priorities, key=lambda x: x["integer_value"])["integer_value"]

    return {
        "tickets": tickets,
        "min_priority": min_priority,
        "max_priority": max_priority,
    }


@frappe.whitelist()
@agent_only
def get_upcoming_sla_violations(priority=None, order_by="response_by asc"):
    filters = [
        ["sla", "!=", ""],
        ["agreement_status", "in", ["First Response Due", "Resolution Due"]],
        ["status_category", "!=", "Closed"],
        ["_assign", "like", f"%{frappe.session.user}%"],
        ["resolution_by", ">", frappe.utils.now()],
        ["response_by", ">", frappe.utils.now()],
    ]
    if priority:
        filters.append(["priority", "=", priority])
    upcoming_sla_violations = frappe.get_list(
        "HD Ticket",
        fields=[
            "name",
            "subject",
            "status",
            "priority",
            "priority.integer_value",
            "agent_group",
            "response_by",
            "resolution_by",
            "resolution_date",
            "agreement_status",
            "status_category",
            "first_responded_on",
        ],
        filters=filters,
        order_by=order_by,
        limit=5,
    )

    priorities = frappe.get_all("HD Ticket Priority", fields="integer_value")
    min_priority = min(priorities, key=lambda x: x["integer_value"])["integer_value"]
    max_priority = max(priorities, key=lambda x: x["integer_value"])["integer_value"]

    return {
        "upcoming_sla_violations": upcoming_sla_violations,
        "min_priority": min_priority,
        "max_priority": max_priority,
    }
