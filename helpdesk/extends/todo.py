import frappe
from frappe import _

from helpdesk.helpdesk.doctype.hd_team.hd_team import get_team_members
from helpdesk.utils import is_admin


def validate_team_assignment(doc, event=None):
    """Block assigning an HD Ticket to an agent outside the ticket's team.

    Every assignment path (picker, command palette, bulk assign, raw API) ends
    up inserting a ToDo, so guarding here covers all of them at once.
    """
    if doc.reference_type != "HD Ticket" or not doc.allocated_to:
        return
    # Assignment rules pick from an admin-configured user list and run inside
    # the ticket's own save, so throwing here would break saving the ticket.
    if doc.assignment_rule or is_admin():
        return
    if not is_assignment_restricted_to_team():
        return

    team = frappe.db.get_value("HD Ticket", doc.reference_name, "agent_group")
    if not team or doc.allocated_to in get_team_members(team):
        return

    frappe.throw(
        _("{0} is not a member of the team {1}.").format(
            frappe.bold(doc.allocated_to), frappe.bold(team)
        ),
        title=_("Not Allowed"),
    )


def is_assignment_restricted_to_team() -> bool:
    """`assign_within_team` only applies while team restrictions are on, and it
    keeps its stored value when the parent setting is switched off."""
    restrict_by_team, assign_within_team = frappe.db.get_value(
        "HD Settings",
        "HD Settings",
        ["restrict_tickets_by_agent_group", "assign_within_team"],
    )
    return bool(restrict_by_team and assign_within_team)
