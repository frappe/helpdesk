"""
Routes tickets raised by an L2 (regional) agent straight to National Support
(L3), instead of letting the normal regional round robin either hand it to
a teammate in the same region or self-assign it back to the raiser --
neither of which is wanted.

Runs at before_insert, ahead of assign_brand_from_email, so the forced
agent_group/support_level here takes priority (assign_brand_from_email only
sets agent_group when it is not already set).
"""

import frappe

NATIONAL_TEAM = "National Support"
NATIONAL_SUPPORT_LEVEL = "L2 - National"

# Teams that do NOT count as "L2" for this purpose.
_NON_L2_TEAMS = {NATIONAL_TEAM, "Engineering Team"}


def _is_l2_agent(email: str) -> bool:
    if not email or not frappe.db.exists("HD Agent", email):
        return False
    teams = frappe.get_all("HD Team Member", filters={"user": email}, pluck="parent")
    return any(team not in _NON_L2_TEAMS for team in teams)


def route_l2_raised_tickets(doc, method=None):
    if doc.get("brand") in ("Admin Central", "F360", "P360"):
        return
    raiser = doc.get("raised_by") or frappe.session.user or ""
    if raiser in ("Guest", "Administrator"):
        return
    if not _is_l2_agent(raiser):
        return

    doc.agent_group = NATIONAL_TEAM
    doc.support_level = NATIONAL_SUPPORT_LEVEL
