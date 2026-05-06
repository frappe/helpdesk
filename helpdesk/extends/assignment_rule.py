import frappe
from frappe import _

from helpdesk.utils import is_json_valid


def on_assignment_rule_trash(doc, event):
    if not frappe.get_all(
        "Assignment Rule",
        filters={"document_type": "HD Ticket", "name": ["!=", doc.name]},
    ):
        frappe.throw("There should atleast be 1 assignment rule for ticket")


def on_assignment_rule_validate(doc, event):
    if doc.assign_condition_json and not is_json_valid(doc.assign_condition_json):
        frappe.throw(
            _("The Assign Condition JSON '{0}' is invalid: </br> {1}").format(
                doc.assign_condition_json,
                "Condition format should be like this e.g [['status','==','open']], it's recommended to use portal view to create conditions.",
            )
        )

    if doc.unassign_condition_json and not is_json_valid(doc.unassign_condition_json):
        frappe.throw(
            _("The Unassign Condition JSON '{0}' is invalid: </br> {1}").format(
                doc.unassign_condition_json,
                "Condition format should be like this e.g [['status','==','open']], it's recommended to use portal view to create conditions.",
            )
        )

    validate_users(doc)


def validate_users(doc):
    """
    When AR's users or weighted_users change, show a message if the AR is linked to a team and the user is not part of the team.
    """
    team_name = frappe.db.get_value("HD Team", {"assignment_rule": doc.name}, "name")
    if not team_name:
        return

    team_agents = frappe.get_all(
        "HD Team Member", filters={"parent": team_name}, pluck="user"
    )

    msg = _(
        "This Assignment Rule is linked to the Team {0}.</br> User {1} is added in the Assignment Rule but not in the linked Team. Please add the user in the {2} to ensure proper team structure."
    )

    if doc.rule == "Weighted Distribution":
        users = [u.user for u in doc.weighted_users if u.user]
        for user in users:
            if user not in team_agents:
                frappe.msgprint(
                    msg.format(
                        f"<a href='/app/hd-team/{team_name}'><b>{team_name}</b></a>",
                        f"<u>{user}</u>",
                        f"<a href='/app/hd-team/{team_name}'><b>{team_name}</b></a>",
                    )
                )

    elif doc.rule == "Round Robin" or doc.rule == "Load Balancing":
        for user in doc.users:
            if user.user not in team_agents:
                frappe.msgprint(
                    msg.format(
                        f"<a href='/app/hd-team/{team_name}'><b>{team_name}</b></a>",
                        f"<u>{user.user}</u>",
                        f"<a href='/app/hd-team/{team_name}'><b>{team_name}</b></a>",
                    )
                )
