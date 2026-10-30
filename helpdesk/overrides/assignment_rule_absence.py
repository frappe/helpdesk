"""
Absence-aware Assignment Rule: agents with an active HD Agent Absence are
skipped when the rule picks a user. No scheduled job is needed. The check is
a date comparison, so assignment resumes by itself on the return date.
If everyone in the rule is away, nothing is assigned (ticket stays unassigned).
"""
import frappe
from frappe.automation.doctype.assignment_rule.assignment_rule import AssignmentRule
from frappe.utils import getdate


def away_users(on=None):
    today = getdate(on)
    return set(frappe.get_all("HD Agent Absence", filters={
        "cancelled": 0, "from_date": ["<=", today], "return_date": [">", today]},
        pluck="user"))


class AbsenceAwareAssignmentRule(AssignmentRule):
    def get_user(self, doc):
        if not frappe.db.exists("DocType", "HD Agent Absence"):
            return super().get_user(doc)
        away = away_users()
        everyone = self.get("users") or []
        if not away or not everyone:
            return super().get_user(doc)

        available = [u for u in everyone if u.user not in away]
        if not available:
            return None
        self.users = available
        try:
            return super().get_user(doc)
        finally:
            self.users = everyone
