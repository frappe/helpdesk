# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from helpdesk.utils import get_agents_team


class HDSavedReply(Document):
    pass


def has_permission(doc, user=None):
    if not user:
        user = frappe.session.user

    user_roles = frappe.get_roles(user)
    is_user_admin = "System Manager" in user_roles or "Agent Manager" in user_roles

    if doc.owner == user or is_user_admin:
        return True

    is_team_restriction_applied = frappe.db.get_single_value(
        "HD Settings", "restrict_tickets_by_agent_group"
    )
    is_global_scope_disabled = frappe.db.get_single_value(
        "HD Settings", "disable_saved_replies_global_scope"
    )

    scope = doc.scope

    if scope == "Global":
        if not is_global_scope_disabled:
            return True

    elif scope == "Team":
        if not is_team_restriction_applied:
            return True
        else:
            user_team = get_agents_team()
            user_team_names = [team["team_name"] for team in user_team]
            if not user_team_names:
                return False

            exists = frappe.db.exists(
                "HD Saved Reply Team",
                {"parent": doc.name, "team": ["in", user_team_names]},
            )
            return bool(exists)

    return False


def permission_query(user):
    if not user:
        user = frappe.session.user

    user_roles = frappe.get_roles(user)
    is_user_admin = "System Manager" in user_roles or "Agent Manager" in user_roles

    if is_user_admin:
        return

    is_team_restriction_applied = frappe.db.get_single_value(
        "HD Settings", "restrict_tickets_by_agent_group"
    )
    is_global_scope_disabled = frappe.db.get_single_value(
        "HD Settings", "disable_saved_replies_global_scope"
    )

    conditions = []
    if not is_global_scope_disabled:
        conditions.append("`tabHD Saved Reply`.scope = 'Global'")

    personal_cond = f"(`tabHD Saved Reply`.scope = 'Personal' AND `tabHD Saved Reply`.owner = {frappe.db.escape(user)})"

    conditions.append(personal_cond)

    team_cond = "`tabHD Saved Reply`.scope = 'Team'"

    if is_team_restriction_applied:
        user_team = get_agents_team()
        user_team_names = [team["team_name"] for team in user_team]
        if user_team_names:
            team_names_escaped = ", ".join(
                f"{frappe.db.escape(team)}" for team in user_team_names
            )
            team_cond = f"(`tabHD Saved Reply`.scope = 'Team' AND `tabHD Saved Reply`.name IN (SELECT parent FROM `tabHD Saved Reply Team` WHERE team IN ({team_names_escaped})))"
        else:
            team_cond = None

    if team_cond:
        conditions.append(team_cond)

    query = " OR ".join(f"({cond})" for cond in conditions)
    return query
