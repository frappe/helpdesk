from datetime import date, timedelta

import frappe
from frappe.query_builder import DocType
from frappe.query_builder.functions import Avg, Function
from frappe.utils import add_days, nowdate

from helpdesk.api.agent_home.utils import calculate_percentage_change

Scope = str  # Literal["agent", "customer", "contact"]


def _apply_scope(query, Ticket, scope: Scope, identifier: str | None):
    """
    Append the appropriate WHERE clause for the given scope.

    Parameters
    ----------
    query      : PyPika query being built
    Ticket     : DocType("HD Ticket") table reference
    scope      : "agent" | "customer" | "contact"
    identifier : agent email / customer name / contact name
    """
    if scope == "agent":
        query = query.where(
            Function(
                "JSON_SEARCH", Ticket._assign, "one", identifier or frappe.session.user
            ).isnotnull()
        )
    elif scope == "customer":
        query = query.where(Ticket.customer == identifier)
    elif scope == "contact":
        query = query.where(Ticket.contact == identifier)
    else:
        frappe.throw(
            f"Invalid scope '{scope}'. Must be 'agent', 'customer', or 'contact'."
        )
    return query


def get_avg_time(
    from_date,
    to_date,
    time_field: str,
    scope: Scope = "agent",
    identifier: str | None = None,
    group_by_date: bool = False,
) -> list:
    """
    Return the average value of *time_field* on HD Ticket rows that fall in
    [from_date, to_date] and match the given scope/identifier.

    When group_by_date=True returns a list of {date, avg_time} dicts.
    When group_by_date=False returns a single-element list [{avg_time: ...}].
    """
    if identifier is None:
        identifier = frappe.session.user

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

    query = (
        query.where(Ticket.creation >= from_date)
        .where(Ticket.creation < to_date_plus_one)
        .where(Ticket[time_field].isnotnull())
    )
    query = _apply_scope(query, Ticket, scope, identifier)

    return query.run(as_dict=True)


def _scalar_avg_time(
    from_date,
    to_date,
    time_field: str,
    scope: Scope,
    identifier: str,
) -> float:
    """Return a single average float (no date grouping)."""
    result = get_avg_time(
        from_date, to_date, time_field, scope, identifier, group_by_date=False
    )
    return (
        result[0]["avg_time"] if result and result[0]["avg_time"] is not None else 0.0
    )


def get_avg_time_metric(
    period: str,
    time_field: str,
    scope: Scope = "agent",
    identifier: str | None = None,
) -> dict:
    """
    Build the avg-time metric dict (data series + average + % change) for a
    given period, time field, and scope.
    """
    resolved: str = identifier or str(frappe.session.user)

    periods = {
        "last week": 7,
        "last month": 30,
        "last 3 months": 90,
        "last 6 months": 180,
    }
    days = periods.get(period, 7)

    current_from = add_days(nowdate(), -(days - 1))
    current_to = nowdate()
    previous_from = add_days(nowdate(), -(2 * days - 1))
    previous_to = add_days(nowdate(), -days)

    current_series = get_avg_time(
        current_from, current_to, time_field, scope, resolved, group_by_date=True
    )
    current_avg = _scalar_avg_time(
        current_from, current_to, time_field, scope, resolved
    )
    previous_avg = _scalar_avg_time(
        previous_from, previous_to, time_field, scope, resolved
    )

    percentage_change = calculate_percentage_change(current_avg, previous_avg)

    # Fill missing days with 0
    from_date_obj = date.fromisoformat(str(current_from))
    to_date_obj = date.fromisoformat(str(current_to))
    date_dict: dict[str, float] = {}
    cur = from_date_obj
    while cur <= to_date_obj:
        date_dict[cur.isoformat()] = 0
        cur += timedelta(days=1)

    for row in current_series:
        date_dict[str(row["date"])] = round(row["avg_time"] or 0, 2)

    data = [
        {"date": d, "avg_time": avg_time} for d, avg_time in sorted(date_dict.items())
    ]

    return {
        "data": data,
        "average": round(current_avg, 2),
        "percentage_change": percentage_change,
    }
