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


def on_assignment_rule_before_save(doc, event):
    """
    When AR's users or weighted_users change, sync back to the linked HD Team.
    Skips if already in sync.
    """
    team_name = frappe.db.get_value("HD Team", {"assignment_rule": doc.name}, "name")
    if not team_name:
        return

    seen = set()
    members = []
    for row in list(doc.users) + list(doc.weighted_users):
        if row.user and row.user not in seen:
            seen.add(row.user)
            members.append(row.user)

    team = frappe.get_doc("HD Team", team_name)
    team_user_set = {u.user for u in team.users if u.user}

    if set(members) == team_user_set:
        return

    team.users = []
    for user in members:
        team.append("users", {"user": user})

    team.save(ignore_permissions=True)
