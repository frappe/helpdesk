# Copyright (c) 2025, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from helpdesk.utils import get_agents_team


class HDSavedReply(Document):
    pass


def permission_query(user):
    if not user:
        user = frappe.session.user

    user_roles = frappe.get_roles(user)
    is_user_admin = "System Manager" in user_roles or "Agent Manager" in user_roles

    is_team_restriction_applied = frappe.db.get_single_value(
        "HD Settings", "restrict_tickets_by_agent_group"
    )

    conditions = []
    conditions.append("`tabHD Saved Reply`.scope = 'Global'")

    if is_user_admin:
        personal_cond = "`tabHD Saved Reply`.scope = 'Personal'"
    else:
        personal_cond = f"(`tabHD Saved Reply`.scope = 'Personal' AND `tabHD Saved Reply`.owner = {frappe.db.escape(user)})"

    conditions.append(personal_cond)

    team_cond = "`tabHD Saved Reply`.scope = 'Team'"

    if is_team_restriction_applied and not is_user_admin:
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
