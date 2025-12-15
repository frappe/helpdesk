import frappe
from frappe import _

from helpdesk.utils import agent_only


def assign_ticket_to_agent(ticket_id, agent_id=None):
    if not ticket_id:
        return

    ticket_doc = frappe.get_doc("HD Ticket", ticket_id)

    if not agent_id:
        # assign to self
        agent_id = frappe.session.user

    if not frappe.db.exists("HD Agent", agent_id):
        frappe.throw(_("Tickets can only be assigned to agents"))

    ticket_doc.assign_agent(agent_id)
    return ticket_doc


@frappe.whitelist()
@agent_only
def bulk_assign_ticket_to_agent(ticket_ids, agent_id=None):
    if ticket_ids:
        ticket_docs = []
        for ticket_id in ticket_ids:
            ticket_doc = assign_ticket_to_agent(ticket_id, agent_id)
            ticket_docs.append(ticket_doc)
        return ticket_docs


@frappe.whitelist()
def get_tickets_for_card_view(
    filters=None,
    limit=20,
    offset=0,
    order_by="name desc"
):
    """
    Optimized API endpoint for fetching tickets in card view.
    Supports filtering by status, priority, team (agent_group), and agent.
    """
    import json

    # Parse filters if they're passed as JSON string
    if isinstance(filters, str):
        filters = json.loads(filters) if filters else {}
    elif filters is None:
        filters = {}

    def build_filters(raw_filters):
        """Convert API filters to frappe.get_list compatible filters."""
        filter_list = []

        status_filter = raw_filters.get("status")
        if isinstance(status_filter, list) and len(status_filter) == 2:
            operator, values = status_filter
            if operator == "in" and isinstance(values, list):
                filter_list.append(["status", "in", values])
            elif operator == "!=":
                filter_list.append(["status", "!=", values])
        elif isinstance(status_filter, str):
            filter_list.append(["status", "=", status_filter])

        priority_filter = raw_filters.get("priority")
        if isinstance(priority_filter, list) and len(priority_filter) == 2:
            operator, values = priority_filter
            if operator == "in" and isinstance(values, list):
                filter_list.append(["priority", "in", values])
        elif isinstance(priority_filter, str):
            filter_list.append(["priority", "=", priority_filter])

        team_filter = raw_filters.get("agent_group")
        if isinstance(team_filter, list) and len(team_filter) == 2:
            operator, values = team_filter
            if operator == "in" and isinstance(values, list):
                filter_list.append(["agent_group", "in", values])
        elif isinstance(team_filter, str):
            filter_list.append(["agent_group", "=", team_filter])

        assign_filter = raw_filters.get("_assign")
        if isinstance(assign_filter, list) and len(assign_filter) == 2:
            operator, value = assign_filter
            if operator == "like":
                filter_list.append(["_assign", "like", value])

        assigned_to = raw_filters.get("assigned_to")
        if assigned_to:
            filter_list.append(["_assign", "like", f'%"{assigned_to}"%'])

        raised_by = raw_filters.get("raised_by")
        if raised_by:
            filter_list.append(["raised_by", "=", raised_by])

        owner = raw_filters.get("owner")
        if owner:
            filter_list.append(["contact", "=", owner])

        return filter_list

    parsed_filters = build_filters(filters)

    # Default to ticket id based ordering so permission queries still apply.
    order_by_value = "name desc"

    tickets = frappe.get_list(
        "HD Ticket",
        filters=parsed_filters,
        fields=[
            "name",
            "subject",
            "status",
            "status_category",
            "priority",
            "creation",
            "modified",
            "raised_by",
            "agent_group",
            "first_responded_on",
            "resolution_date",
            "response_by",
            "resolution_by",
            "agreement_status",
            "contact",
            "_assign",
            "_liked_by",
            "_comments",
        ],
        limit_start=int(offset),
        limit_page_length=int(limit),
        order_by=order_by_value,
        as_list=False,
    )

    # Permission-aware count using get_list to ensure user permissions are applied
    total_count_result = frappe.get_list(
        "HD Ticket",
        filters=parsed_filters,
        fields=["count(name) as total_count"]
    )
    total_count = total_count_result[0].get("total_count", 0) if total_count_result else 0

    return {
        "data": tickets,
        "total_count": total_count,
        "limit": int(limit),
        "offset": int(offset),
    }
