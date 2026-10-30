"""
Permission scoping for HD Agent list/search (the "assignee" picker).

Regional/frontline agents should only see other agents who share at least
one HD Team with them -- e.g. a Western Region agent should not see Nyanza
Region agents, and should not be able to hand-pick a National Support (L3)
person directly out of the assignee search.

National Support (L3) members are the one exception: they see every agent,
matching the "L3 sees everyone" rule already enforced on HD Ticket
visibility (team_hierarchy.py).
"""

import frappe

from helpdesk.utils import is_admin, is_agent

NATIONAL_TEAM = "National Support"


def _is_national_member(user: str) -> bool:
    return bool(frappe.db.exists("HD Team Member", {"parent": NATIONAL_TEAM, "user": user}))


def _user_teams(user: str) -> list:
    return frappe.get_all("HD Team Member", filters={"user": user}, pluck="parent")


def has_permission(doc, user=None):
    if not user:
        user = frappe.session.user

    if is_admin(user):
        return True

    if not is_agent(user):
        return False

    if doc.user == user:
        return True

    if _is_national_member(user):
        return True

    my_teams = _user_teams(user)
    if not my_teams:
        return False

    their_teams = _user_teams(doc.user)
    return bool(set(my_teams) & set(their_teams))


def permission_query(user):
    if not user:
        user = frappe.session.user

    if is_admin(user):
        return

    if not is_agent(user):
        return "1=0"

    if _is_national_member(user):
        return  # no restriction -- National Support sees every agent

    my_teams = _user_teams(user)
    if not my_teams:
        return "`tabHD Agent`.user = {user}".format(user=frappe.db.escape(user))

    team_list = ", ".join(frappe.db.escape(t) for t in my_teams)
    return (
        "(`tabHD Agent`.user = {user} OR `tabHD Agent`.user IN ("
        "SELECT htm.user FROM `tabHD Team Member` htm "
        "WHERE htm.parent IN ({team_list})"
        "))"
    ).format(user=frappe.db.escape(user), team_list=team_list)
