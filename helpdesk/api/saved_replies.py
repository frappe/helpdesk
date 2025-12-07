import frappe
from frappe import _

from helpdesk.utils import get_agents_team, is_admin


@frappe.whitelist()
def get_saved_replies(scope):
    QBEmailTemplate = frappe.qb.DocType("Email Template")
    QBChildTeam = frappe.qb.DocType("HD Saved Reply Team")
    is_team_restriction_applied = frappe.db.get_single_value(
        "HD Settings", "restrict_tickets_by_agent_group"
    )

    base_query = (
        frappe.qb.from_(QBEmailTemplate)
        .left_join(QBChildTeam)
        .on(QBChildTeam.parent == QBEmailTemplate.name)
        .select(QBEmailTemplate.star, QBChildTeam.team)
        .where(QBEmailTemplate.reference_doctype == "HD Ticket")
        .groupby(QBEmailTemplate.name)
    )

    if scope == "Global":
        query = base_query.where(QBEmailTemplate.scope == "Global")
    elif scope == "Personal":
        query = base_query.where(
            (QBEmailTemplate.scope == "Personal")
            & (QBEmailTemplate.owner == frappe.session.user)
        )
    elif scope == "My Team":
        user_team = get_agents_team()
        user_team_names = [team["team_name"] for team in user_team]
        if not user_team_names:
            return []
        query = base_query.where(
            (QBEmailTemplate.scope == "Team") & (QBChildTeam.team.isin(user_team_names))
        )
    elif scope == "All":
        if is_team_restriction_applied:
            user_team = get_agents_team()
            user_team_names = [team["team_name"] for team in user_team]
            if not user_team_names:
                return []

            if is_admin():
                query = base_query
            else:
                query = base_query.where(
                    (
                        (QBEmailTemplate.scope == "Team")
                        & (QBChildTeam.team.isin(user_team_names))
                    )
                    | (
                        (QBEmailTemplate.scope == "Personal")
                        & (QBEmailTemplate.owner == frappe.session.user)
                    )
                )
        else:
            query = base_query

    return query.run(as_dict=True)


@frappe.whitelist()
def get_rendered_saved_reply(ticket_id, saved_reply_id=None, saved_reply=None):
    if not (saved_reply_id or saved_reply):
        frappe.throw(_("Please provide either saved_reply_id or saved_reply data"))
    if not saved_reply:
        saved_reply = frappe.get_doc("Email Template", saved_reply_id).response
    ticket = frappe.get_doc("HD Ticket", ticket_id).as_dict()
    user = frappe.get_doc("User", frappe.session.user).as_dict()
    return frappe.render_template(saved_reply, {**ticket, **user})
