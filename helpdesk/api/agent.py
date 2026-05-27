import frappe
from frappe import _
from frappe.query_builder import DocType
from frappe.query_builder.functions import Avg, Count

from helpdesk.utils import agent_only


@frappe.whitelist()
@agent_only
def sent_invites(emails: list[str], send_welcome_mail_to_user: bool = True):
    for email in emails:
        if frappe.db.exists("User", email):
            user = frappe.get_doc("User", email)
        else:
            user = frappe.get_doc(
                {"doctype": "User", "email": email, "first_name": email.split("@")[0]}
            ).insert()

            if send_welcome_mail_to_user:
                user.send_welcome_mail_to_user()

        frappe.get_doc(
            {
                "doctype": "HD Agent",
                "ID": email,
                "user": user.name,
                "agent_name": user.full_name,
                "user_image": user.user_image,
            }
        ).insert()
    return


@frappe.whitelist()
@agent_only
def get_availability_options() -> list[str]:
    options = frappe.get_meta("HD Agent").get_field("availability").options or ""
    return [o.strip() for o in options.split("\n") if o.strip()]


def _agent_name_for_session() -> str | None:
    return frappe.db.get_value("HD Agent", {"user": frappe.session.user}, "name")


@frappe.whitelist()
@agent_only
def get_my_availability() -> dict:
    name = _agent_name_for_session()
    availability = (
        frappe.db.get_value("HD Agent", name, "availability") if name else None
    )
    return {
        "availability": availability,
        "options": get_availability_options(),
    }


@frappe.whitelist()
@agent_only
def set_my_availability(availability: str) -> dict:
    if availability not in get_availability_options():
        frappe.throw(_("Invalid availability"), frappe.ValidationError)

    name = _agent_name_for_session()
    if not name:
        frappe.throw(_("No HD Agent record for current user"), frappe.ValidationError)

    frappe.db.set_value(
        "HD Agent",
        name,
        {"availability": availability, "availability_changed_on": frappe.utils.now()},
    )
    return {"availability": availability}


@frappe.whitelist()
@agent_only
def get_agent_workload(user_ids: list[str]) -> dict:
    """
    Per-agent workload stats for the Agents settings page.

    Returns a dict keyed by user id with the fields used by the Agents
    settings list: open_tickets (+ delta vs 7d ago), average_first_response_seconds
    (+ delta vs the previous 7d window), teams, team_open_tickets.

    `team_open_tickets` is the denominator for the "X of N" load display:
    the union of open tickets assigned to any member of any team the agent
    belongs to. Zero when the agent is on no team.
    """
    if not user_ids:
        return {}

    teams_per_user, members_per_team = _team_membership(user_ids)
    teammate_universe = set(user_ids) | {
        u for members in members_per_team.values() for u in members
    }

    week_ago = frappe.utils.add_days(frappe.utils.today(), -7)
    two_weeks_ago = frappe.utils.add_days(frappe.utils.today(), -14)

    open_per_user = _open_tickets_per_user(list(teammate_universe))
    open_week_ago_per_user = _open_tickets_as_of(user_ids, week_ago)
    resolved_per_user = _resolved_today_per_user(user_ids)
    response_per_user = _average_first_response_window(user_ids, week_ago, None)
    response_previous_per_user = _average_first_response_window(
        user_ids, two_weeks_ago, week_ago
    )

    result = {}
    for user in user_ids:
        teammate_set = {
            u
            for team in teams_per_user.get(user, set())
            for u in members_per_team.get(team, set())
        }
        open_now = open_per_user.get(user, 0)
        response_now = response_per_user.get(user, 0)
        result[user] = {
            "open_tickets": open_now,
            "open_tickets_delta": open_now - open_week_ago_per_user.get(user, 0),
            "resolved_today": resolved_per_user.get(user, 0),
            "average_first_response_seconds": response_now,
            "average_first_response_seconds_delta": (
                response_now - response_previous_per_user.get(user, 0)
                if response_now and response_previous_per_user.get(user, 0)
                else 0
            ),
            "teams": sorted(teams_per_user.get(user, set())),
            "team_open_tickets": sum(open_per_user.get(u, 0) for u in teammate_set),
        }
    return result


def _team_membership(user_ids: list[str]) -> tuple[dict, dict]:
    TeamMember = DocType("HD Team Member")
    rows = (
        frappe.qb.from_(TeamMember)
        .select(TeamMember.user, TeamMember.parent.as_("team"))
        .where(TeamMember.user.isin(user_ids))
        .where(TeamMember.parenttype == "HD Team")
    ).run(as_dict=True)

    teams_per_user: dict[str, set[str]] = {}
    for row in rows:
        teams_per_user.setdefault(row["user"], set()).add(row["team"])

    all_teams = {t for teams in teams_per_user.values() for t in teams}
    members_per_team: dict[str, set[str]] = {}
    if all_teams:
        member_rows = (
            frappe.qb.from_(TeamMember)
            .select(TeamMember.user, TeamMember.parent.as_("team"))
            .where(TeamMember.parent.isin(list(all_teams)))
            .where(TeamMember.parenttype == "HD Team")
        ).run(as_dict=True)
        for row in member_rows:
            members_per_team.setdefault(row["team"], set()).add(row["user"])

    return teams_per_user, members_per_team


def _open_tickets_per_user(user_ids: list[str]) -> dict[str, int]:
    if not user_ids:
        return {}
    Ticket = DocType("HD Ticket")
    ToDo = DocType("ToDo")
    resolved_statuses = frappe.get_all(
        "HD Ticket Status", filters={"category": "Resolved"}, pluck="name"
    )
    query = (
        frappe.qb.from_(ToDo)
        .join(Ticket)
        .on((ToDo.reference_type == "HD Ticket") & (ToDo.reference_name == Ticket.name))
        .select(ToDo.allocated_to.as_("user"), Count(ToDo.name).as_("count"))
        .where(ToDo.allocated_to.isin(user_ids))
        .where(ToDo.status == "Open")
        .groupby(ToDo.allocated_to)
    )
    if resolved_statuses:
        query = query.where(Ticket.status.notin(resolved_statuses))
    return {row["user"]: row["count"] for row in query.run(as_dict=True)}


def _resolved_today_per_user(user_ids: list[str]) -> dict[str, int]:
    Ticket = DocType("HD Ticket")
    ToDo = DocType("ToDo")
    resolved_statuses = frappe.get_all(
        "HD Ticket Status", filters={"category": "Resolved"}, pluck="name"
    )
    query = (
        frappe.qb.from_(ToDo)
        .join(Ticket)
        .on((ToDo.reference_type == "HD Ticket") & (ToDo.reference_name == Ticket.name))
        .select(ToDo.allocated_to.as_("user"), Count(Ticket.name).as_("count"))
        .where(ToDo.allocated_to.isin(user_ids))
        .where(Ticket.resolution_date >= frappe.utils.today())
        .groupby(ToDo.allocated_to)
    )
    if resolved_statuses:
        query = query.where(Ticket.status.isin(resolved_statuses))
    return {row["user"]: row["count"] for row in query.run(as_dict=True)}


def _average_first_response_window(
    user_ids: list[str], start: str, end: str | None
) -> dict[str, int]:
    """Avg first response seconds for tickets first-responded in [start, end)."""
    Ticket = DocType("HD Ticket")
    ToDo = DocType("ToDo")
    query = (
        frappe.qb.from_(ToDo)
        .join(Ticket)
        .on((ToDo.reference_type == "HD Ticket") & (ToDo.reference_name == Ticket.name))
        .select(
            ToDo.allocated_to.as_("user"),
            Avg(Ticket.first_response_time).as_("average_seconds"),
        )
        .where(ToDo.allocated_to.isin(user_ids))
        .where(Ticket.first_responded_on >= start)
        .groupby(ToDo.allocated_to)
    )
    if end:
        query = query.where(Ticket.first_responded_on < end)
    return {
        row["user"]: round(row["average_seconds"] or 0)
        for row in query.run(as_dict=True)
    }


def _open_tickets_as_of(user_ids: list[str], as_of: str) -> dict[str, int]:
    """
    Count of currently-assigned tickets that were open on `as_of`.
    Approximation: assumes current assignee was the assignee then; treats a
    ticket as open at `as_of` if it was created on/before that date and not
    yet resolved (or resolved after).
    """
    if not user_ids:
        return {}
    Ticket = DocType("HD Ticket")
    ToDo = DocType("ToDo")
    query = (
        frappe.qb.from_(ToDo)
        .join(Ticket)
        .on((ToDo.reference_type == "HD Ticket") & (ToDo.reference_name == Ticket.name))
        .select(ToDo.allocated_to.as_("user"), Count(ToDo.name).as_("count"))
        .where(ToDo.allocated_to.isin(user_ids))
        .where(Ticket.creation <= as_of)
        .where((Ticket.resolution_date.isnull()) | (Ticket.resolution_date > as_of))
        .groupby(ToDo.allocated_to)
    )
    return {row["user"]: row["count"] for row in query.run(as_dict=True)}
