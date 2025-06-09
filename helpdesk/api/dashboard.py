import frappe

from helpdesk.utils import agent_only


@agent_only
@frappe.whitelist()
def get_dashboard_data(type, filters=None):
    """
    Get dashboard data based on the type and date range.
    """
    from_date = filters.get("from_date") if filters else None
    to_date = filters.get("to_date") if filters else None
    team = filters.get("team") if filters else None
    agent = filters.get("agent") if filters else None

    if not from_date:
        from_date = frappe.utils.add_days(frappe.utils.nowdate(), -30)
    if not to_date:
        to_date = frappe.utils.nowdate()

    if type == "number_card":
        return get_number_card_data(from_date, to_date)
    elif type == "master":
        print("Master Dashboard Data")
    elif type == "trend":
        print("\n\n", "TREND", "\n\n")


def get_number_card_data(from_date, to_date):
    """
    Get number card data for the dashboard.
    """
    from_date = frappe.utils.add_days(frappe.utils.nowdate(), -30)
    to_date = frappe.utils.nowdate()
    # Remove from and to date after testing

    ticket_chart_data = get_ticket_count(from_date, to_date)
    avg_feedback_score = get_avg_feedback_score(from_date, to_date)

    return [ticket_chart_data, avg_feedback_score]


def get_ticket_count(from_date, to_date):
    """
    Get ticket data for the dashboard.
    """
    ticket_count = frappe.get_list(
        "HD Ticket",
        filters=[
            {"creation": [">=", from_date]},
            {"creation": ["<=", to_date]},
        ],
        fields=["count(*) as count"],
    )
    ticket_count = ticket_count[0].count if ticket_count else 0
    ticket_count_last_month = frappe.get_list(
        "HD Ticket",
        filters=[
            {"creation": [">=", frappe.utils.add_months(from_date, -1)]},
            {"creation": ["<", from_date]},
        ],
        fields=["count(*) as count"],
    )

    ticket_count_last_month = (
        ticket_count_last_month[0].count if ticket_count_last_month else 0
    )

    delta_in_percentage = (
        (ticket_count - ticket_count_last_month) / ticket_count_last_month * 100
        if ticket_count_last_month
        else 0
    )

    result = frappe.db.sql(
        """
		SELECT
				COUNT(CASE
					WHEN creation >= %(from_date)s AND creation <= %(to_date)s 
					THEN name
					ELSE NULL
				END) as current_month_count

				COUNT(CASE
					WHEN creation >= %(prev_from_date)s AND creation < %(from_date)s 
					THEN name
					ELSE NULL
				END) as prev_month_count
		FROM `tabHD Ticket`
    """,
        {
            "from_date": from_date,
            "to_date": to_date,
            "prev_from_date": frappe.utils.add_months(from_date, -1),
        },
        as_dict=1,
    )

    return {
        "title": "Tickets",
        "value": ticket_count,
        "delta": delta_in_percentage,
        "deltaSuffix": "%",
        "negativeIsBetter": True,
    }


def get_avg_feedback_score(from_date, to_date):
    """
    Get average feedback score for the dashboard.
    """
    from_date = frappe.utils.add_days(frappe.utils.nowdate(), -30)
    to_date = frappe.utils.nowdate()
    result = frappe.db.sql(
        """
        SELECT 
            AVG(CASE 
                WHEN creation >= %(from_date)s AND creation <= %(to_date)s  AND feedback_rating != ''
                THEN feedback_rating 
                ELSE NULL
            END) as current_month_avg,
            AVG(CASE 
                WHEN creation >= %(prev_from_date)s AND creation < %(from_date)s AND feedback_rating != ''
                THEN feedback_rating 
                ELSE NULL
            END) as prev_month_avg
        FROM `tabHD Ticket`
        WHERE 
            (creation >= %(prev_from_date)s AND creation <= %(to_date)s)
            AND feedback_rating IS NOT NULL
    """,
        {
            "from_date": from_date,
            "to_date": to_date,
            "prev_from_date": frappe.utils.add_months(from_date, -1),
        },
        as_dict=1,
    )

    current_month_avg = result[0].current_month_avg or 0
    prev_month_avg = result[0].prev_month_avg or 0

    delta_in_percentage = (
        (current_month_avg - prev_month_avg) / prev_month_avg * 100
        if prev_month_avg
        else 0
    )

    return {
        "title": "Avg. Feedback Rating",
        "value": current_month_avg,
        "suffix": "/5",
        "delta": delta_in_percentage,
        "deltaSuffix": "%",
    }


def get_resolved_tickets(from_date, to_date):
    """
    Get resolved tickets for the dashboard.
    """
    resolved_tickets = frappe.get_list(
        "HD Ticket",
        filters=[
            {"creation": [">=", from_date]},
            {"creation": ["<=", to_date]},
            {"status": ["in", ["Resolved", "Closed"]]},
        ],
        fields=["count(*) as count"],
    )
    resolved_tickets_count = resolved_tickets[0].count if resolved_tickets else 0
    return {
        "title": " %Resolved",
        "value": 2,
    }
