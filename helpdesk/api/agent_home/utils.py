import frappe
from frappe.query_builder import DocType
from pypika.functions import Count


def get_default_agent_dashboard():
    return '[{"chart":"avg_resolution_time","layout":{"x":33,"y":0,"w":17,"h":10,"minW":16,"minH":10,"maxH":11}},{"chart":"avg_first_response_time","layout":{"x":16,"y":0,"w":17,"h":10,"minW":16,"minH":10,"maxH":11}},{"chart":"agent_tickets","layout":{"x":0,"y":0,"w":16,"h":10,"minW":16,"minH":10,"maxH":11}},{"chart":"pending_tickets","layout":{"x":0,"y":10,"w":50,"h":32,"minW":25,"minH":32,"maxH":32}},{"chart":"recent_feedback","layout":{"x":0,"y":66,"w":50,"h":21,"minW":50,"minH":21,"maxH":21}},{"chart":"avg_time_metrics","layout":{"x":0,"y":42,"w":50,"h":24,"minW":18,"minH":24,"maxH":44}}]'


def calculate_percentage_change(current_value: float, previous_value: float) -> float:
    """
    Calculate the percentage change between two values.
    Returns 999 when there's no previous value but there is a current value.
    Returns 0 when both values are zero.
    """
    if previous_value > 0:
        return round(((current_value - previous_value) / previous_value) * 100, 2)
    elif current_value > 0:
        return 999
    return 0


def get_ticket_count(filters: list) -> int:
    ticket = DocType("HD Ticket")
    query = frappe.qb.from_(ticket).select(Count(ticket.name).as_("count"))

    for f in filters:
        if len(f) == 2:
            field, value = f
            operator = "="
        else:
            field, operator, value = f

        if operator == "=":
            query = query.where(ticket[field] == value)
        elif operator == "!=":
            query = query.where(ticket[field] != value)
        elif operator.lower() == "in":
            query = query.where(ticket[field].isin(value))
        elif operator.lower() == "not in":
            query = query.where(ticket[field].notin(value))
        elif operator.lower() == "like":
            query = query.where(ticket[field].like(value))
        elif operator.lower() == "not like":
            query = query.where(ticket[field].not_like(value))
        elif operator.lower() == "is":
            if value.lower() == "set":
                query = query.where(ticket[field].isnotnull() & (ticket[field] != ""))
            elif value.lower() == "not set":
                query = query.where(ticket[field].isnull() | (ticket[field] == ""))

    result = query.run(as_dict=True)
    return result[0]["count"] if result else 0
