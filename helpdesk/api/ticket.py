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
    Supports filtering by status, priority, team (agent_group), agent, search, and date ranges.
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
            # Owner refers to the ticket owner (User), not the contact.
            # Align with list view / dashboard semantics so counts and
            # card-view results stay consistent.
            filter_list.append(["owner", "=", owner])

        # Date range / creation filters (from dashboard duration or query params)
        creation_filter = raw_filters.get("creation")
        if isinstance(creation_filter, list) and len(creation_filter) == 2:
            operator, value = creation_filter
            if isinstance(operator, str):
                operator = operator.lower()
            # Between date range: ["between", [from_date, to_date]]
            if operator == "between" and isinstance(value, list) and len(value) == 2:
                filter_list.append(["creation", "between", value])
            # Direct comparisons: [">=", date], ["<=", date], etc.
            elif operator in (">=", "<=", ">", "<", "="):
                filter_list.append(["creation", operator, value])

        # Resolution date filters (actual resolved timestamp)
        resolution_date_filter = raw_filters.get("resolution_date")
        if isinstance(resolution_date_filter, list) and len(resolution_date_filter) == 2:
            operator, value = resolution_date_filter
            if isinstance(operator, str):
                operator = operator.lower()
            if operator == "between" and isinstance(value, list) and len(value) == 2:
                filter_list.append(["resolution_date", "between", value])
            elif operator in (">=", "<=", ">", "<", "="):
                filter_list.append(["resolution_date", operator, value])

        # Resolution by filter (for overdue/resolved tickets)
        resolution_by_filter = raw_filters.get("resolution_by")
        resolution_by_set_flag = raw_filters.get("_resolution_by", False) or raw_filters.get("resolution_by", False) is True
        
        if isinstance(resolution_by_filter, list) and len(resolution_by_filter) == 2:
            operator, value = resolution_by_filter
            if isinstance(operator, str):
                operator = operator.lower()
            if operator in (">=", "<=", ">", "<", "="):
                filter_list.append(["resolution_by", operator, value])
            # Handle "between" operator for date range queries
            elif operator == "between" and isinstance(value, list) and len(value) == 2:
                filter_list.append(["resolution_by", "between", value])
            # If "is" operator, add as is set check
            elif operator == "is" and value == "set":
                filter_list.append(["resolution_by", "is", "set"])
        
        # If _resolution_by flag is True, ensure resolution_by is set
        # Check if we haven't already added an "is set" filter
        if resolution_by_set_flag and not any(f[0] == "resolution_by" and len(f) > 1 and f[1] == "is" for f in filter_list):
            filter_list.append(["resolution_by", "is", "set"])

        return filter_list

    parsed_filters = build_filters(filters)

    search_text = ""
    if isinstance(filters, dict):
        search_text = filters.get("search") or filters.get("search_text") or ""
    search_text = (search_text or "").strip()
    or_filters = []
    if search_text:
        like_value = f"%{search_text}%"
        or_filters = [
            ["name", "like", like_value],
            ["subject", "like", like_value],
            ["raised_by", "like", like_value],
            ["contact", "like", like_value],
            ["customer", "like", like_value],
        ]

    # Default to ticket id based ordering so permission queries still apply.
    order_by_value = "name desc"

    tickets = frappe.get_list(
        "HD Ticket",
        filters=parsed_filters,
        or_filters=or_filters,
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
        or_filters=or_filters,
        fields=["count(name) as total_count"]
    )
    total_count = total_count_result[0].get("total_count", 0) if total_count_result else 0

    return {
        "data": tickets,
        "total_count": total_count,
        "limit": int(limit),
        "offset": int(offset),
    }
