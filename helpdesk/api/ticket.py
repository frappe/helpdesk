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
    order_by="modified desc"
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
    
    # Build the query using frappe.qb
    Ticket = frappe.qb.DocType("HD Ticket")
    query = frappe.qb.from_(Ticket).select(
        Ticket.name,
        Ticket.subject,
        Ticket.status,
        Ticket.status_category,
        Ticket.priority,
        Ticket.creation,
        Ticket.modified,
        Ticket.raised_by,
        Ticket.agent_group,
        Ticket.first_responded_on,
        Ticket.resolution_date,
        Ticket.response_by,
        Ticket.resolution_by,
        Ticket.agreement_status,
        Ticket.contact,
        Ticket._assign,
        Ticket._liked_by,
        Ticket._comments
    )
    
    # Apply filters
    # Status filter
    if "status" in filters:
        status_filter = filters["status"]
        if isinstance(status_filter, list) and len(status_filter) == 2:
            operator, values = status_filter
            if operator == "in" and isinstance(values, list):
                query = query.where(Ticket.status.isin(values))
            elif operator == "!=":
                query = query.where(Ticket.status != values)
        elif isinstance(status_filter, str):
            query = query.where(Ticket.status == status_filter)
    
    # Priority filter
    if "priority" in filters:
        priority_filter = filters["priority"]
        if isinstance(priority_filter, list) and len(priority_filter) == 2:
            operator, values = priority_filter
            if operator == "in" and isinstance(values, list):
                query = query.where(Ticket.priority.isin(values))
        elif isinstance(priority_filter, str):
            query = query.where(Ticket.priority == priority_filter)
    
    # Team filter (agent_group)
    if "agent_group" in filters:
        team_filter = filters["agent_group"]
        if isinstance(team_filter, list) and len(team_filter) == 2:
            operator, values = team_filter
            if operator == "in" and isinstance(values, list):
                query = query.where(Ticket.agent_group.isin(values))
        elif isinstance(team_filter, str):
            query = query.where(Ticket.agent_group == team_filter)
    
    # Agent filter (_assign field)
    if "_assign" in filters:
        assign_filter = filters["_assign"]
        if isinstance(assign_filter, list) and len(assign_filter) == 2:
            operator, value = assign_filter
            if operator == "like":
                query = query.where(Ticket._assign.like(value))
    
    # Assigned to filter
    if "assigned_to" in filters:
        assigned_to = filters["assigned_to"]
        if assigned_to:
            query = query.where(Ticket._assign.like(f'%"{assigned_to}"%'))
    
    # Raised by filter
    if "raised_by" in filters:
        raised_by = filters["raised_by"]
        if raised_by:
            query = query.where(Ticket.raised_by == raised_by)
    
    # Owner filter - compare with contact field
    if "owner" in filters:
        owner = filters["owner"]
        if owner:
            query = query.where(Ticket.contact == owner)
    
    # Date range filter (creation date)
    if "creation" in filters:
        creation_filter = filters["creation"]
        if isinstance(creation_filter, list) and len(creation_filter) == 2:
            operator, value = creation_filter
            if operator == "between" and isinstance(value, list) and len(value) == 2:
                from_date, to_date = value
                query = query.where(Ticket.creation >= from_date)
                query = query.where(Ticket.creation <= to_date)
            elif operator == ">=":
                query = query.where(Ticket.creation >= value)
            elif operator == "<=":
                query = query.where(Ticket.creation <= value)
            elif operator == ">":
                query = query.where(Ticket.creation > value)
            elif operator == "<":
                query = query.where(Ticket.creation < value)
    
    # Check if "All" filter is applied (no status filter)
    is_all_filter = "status" not in filters or not filters.get("status")
    
    # Order by - if "All" filter, sort by status category first
    if is_all_filter:
        # Custom sorting: Open (0) -> Paused (1) -> Resolved (2)
        # Use CASE statement for category-based sorting
        from pypika import Case
        
        category_order = (
            Case()
            .when(Ticket.status_category == "Open", 0)
            .when(Ticket.status_category == "Paused", 1)
            .when(Ticket.status_category == "Resolved", 2)
            .else_(3)
        )
        
        query = query.orderby(category_order)
        
        # Then order by modified desc as secondary sort
        query = query.orderby(Ticket.modified, order=frappe.qb.desc)
    elif order_by:
        # Parse order_by string (e.g., "modified desc")
        order_parts = order_by.split()
        if len(order_parts) == 2:
            field_name, direction = order_parts
            order_field = getattr(Ticket, field_name, Ticket.modified)
            if direction.lower() == "desc":
                query = query.orderby(order_field, order=frappe.qb.desc)
            else:
                query = query.orderby(order_field, order=frappe.qb.asc)
        else:
            query = query.orderby(Ticket.modified, order=frappe.qb.desc)
    else:
        query = query.orderby(Ticket.modified, order=frappe.qb.desc)
    
    # Get total count before applying limit/offset
    from pypika import functions as fn
    count_query = frappe.qb.from_(Ticket).select(fn.Count("*"))
    
    # Apply same filters to count query
    if "status" in filters:
        status_filter = filters["status"]
        if isinstance(status_filter, list) and len(status_filter) == 2:
            operator, values = status_filter
            if operator == "in" and isinstance(values, list):
                count_query = count_query.where(Ticket.status.isin(values))
            elif operator == "!=":
                count_query = count_query.where(Ticket.status != values)
        elif isinstance(status_filter, str):
            count_query = count_query.where(Ticket.status == status_filter)
    
    if "priority" in filters:
        priority_filter = filters["priority"]
        if isinstance(priority_filter, list) and len(priority_filter) == 2:
            operator, values = priority_filter
            if operator == "in" and isinstance(values, list):
                count_query = count_query.where(Ticket.priority.isin(values))
        elif isinstance(priority_filter, str):
            count_query = count_query.where(Ticket.priority == priority_filter)
    
    if "agent_group" in filters:
        team_filter = filters["agent_group"]
        if isinstance(team_filter, list) and len(team_filter) == 2:
            operator, values = team_filter
            if operator == "in" and isinstance(values, list):
                count_query = count_query.where(Ticket.agent_group.isin(values))
        elif isinstance(team_filter, str):
            count_query = count_query.where(Ticket.agent_group == team_filter)
    
    if "_assign" in filters:
        assign_filter = filters["_assign"]
        if isinstance(assign_filter, list) and len(assign_filter) == 2:
            operator, value = assign_filter
            if operator == "like":
                count_query = count_query.where(Ticket._assign.like(value))
    
    if "assigned_to" in filters:
        assigned_to = filters["assigned_to"]
        if assigned_to:
            count_query = count_query.where(Ticket._assign.like(f'%"{assigned_to}"%'))
    
    if "raised_by" in filters:
        raised_by = filters["raised_by"]
        if raised_by:
            count_query = count_query.where(Ticket.raised_by == raised_by)
    
    if "owner" in filters:
        owner = filters["owner"]
        if owner:
            count_query = count_query.where(Ticket.contact == owner)
    
    if "creation" in filters:
        creation_filter = filters["creation"]
        if isinstance(creation_filter, list) and len(creation_filter) == 2:
            operator, value = creation_filter
            if operator == "between" and isinstance(value, list) and len(value) == 2:
                from_date, to_date = value
                count_query = count_query.where(Ticket.creation >= from_date)
                count_query = count_query.where(Ticket.creation <= to_date)
            elif operator == ">=":
                count_query = count_query.where(Ticket.creation >= value)
            elif operator == "<=":
                count_query = count_query.where(Ticket.creation <= value)
            elif operator == ">":
                count_query = count_query.where(Ticket.creation > value)
            elif operator == "<":
                count_query = count_query.where(Ticket.creation < value)
    
    total_count = count_query.run()[0][0] if count_query.run() else 0
    
    # Apply limit and offset
    query = query.limit(int(limit)).offset(int(offset))
    
    # Execute query
    tickets = query.run(as_dict=True)
    
    return {
        "data": tickets,
        "total_count": total_count,
        "limit": int(limit),
        "offset": int(offset)
    }
