import frappe
from frappe import _

from helpdesk.utils import get_agents_team


@frappe.whitelist()
def get_canned_responses(teams=None):
    user_team = get_agents_team()
    user_team_names = [team["team_name"] for team in user_team]

    if isinstance(teams, list):
        user_team_names = teams

    QBEmailTemplate = frappe.qb.DocType("Email Template")
    QBChildTeam = frappe.qb.DocType("HD Canned Response Team")
    if user_team_names:
        if "No team" in user_team_names:
            query = (
                frappe.qb.from_(QBEmailTemplate)
                .left_join(QBChildTeam)
                .on(QBChildTeam.parent == QBEmailTemplate.name)
                .select(QBEmailTemplate.star, QBChildTeam.team)
                .where(QBEmailTemplate.reference_doctype == "HD Ticket")
                .where(
                    (QBChildTeam.team.isin(user_team_names))
                    | (QBChildTeam.team.isnull())
                )
            )
        else:
            query = (
                frappe.qb.from_(QBEmailTemplate)
                .left_join(QBChildTeam)
                .on(QBChildTeam.parent == QBEmailTemplate.name)
                .select(QBEmailTemplate.star, QBChildTeam.team)
                .where(QBEmailTemplate.reference_doctype == "HD Ticket")
                .where(QBChildTeam.team.isin(user_team_names))
            )
    else:
        return []

    results = query.run(as_dict=True)
    unique_templates = {}
    for row in results:
        name = row["name"]
        if name not in unique_templates:
            unique_templates[name] = row.copy()
            unique_templates[name]["teams"] = []
        if row.get("team"):
            unique_templates[name]["teams"].append(row["team"])
        if "team" in unique_templates[name]:
            del unique_templates[name]["team"]
    return list(unique_templates.values())


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
