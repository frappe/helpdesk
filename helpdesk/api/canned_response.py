import frappe
from frappe import _

from helpdesk.utils import get_agents_team


@frappe.whitelist()
def get_canned_responses(scope):
    QBEmailTemplate = frappe.qb.DocType("Email Template")
    QBChildTeam = frappe.qb.DocType("HD Canned Response Team")

    base_query = (
        frappe.qb.from_(QBEmailTemplate)
        .left_join(QBChildTeam)
        .on(QBChildTeam.parent == QBEmailTemplate.name)
        .select(QBEmailTemplate.star, QBChildTeam.team)
        .where(QBEmailTemplate.reference_doctype == "HD Ticket")
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

        query = base_query.where(
            (QBEmailTemplate.scope == "Team") & (QBChildTeam.team.isin(user_team_names))
        )

    results = query.run(as_dict=True)
    return results


@frappe.whitelist()
def get_rendered_canned_response(
    ticket_id, canned_response_id=None, canned_response=None
):
    if not (canned_response_id or canned_response):
        frappe.throw(
            _("Please provide either canned_response_id or canned_response data")
        )
    if not canned_response:
        canned_response = frappe.get_doc("Email Template", canned_response_id).response
    ticket = frappe.get_doc("HD Ticket", ticket_id).as_dict()
    user = frappe.get_doc("User", frappe.session.user).as_dict()
    return frappe.render_template(canned_response, {**ticket, **user})
