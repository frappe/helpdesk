import frappe
from frappe.automation.doctype.assignment_rule.assignment_rule import AssignmentRule


def get_away_agents() -> set[str]:
    """User ids of HD Agents currently marked 'Away'."""
    return set(
        frappe.get_all(
            "HD Agent",
            filters={"availability": "Away"},
            pluck="user",
        )
    )


class HelpdeskAssignmentRule(AssignmentRule):
    def get_user(self, doc):
        """
        Override get_user method from framework

        Filter out away agents from normal users present in the assignment rule

        if all agents are on away status resort to the normal pool of users

        """

        away = get_away_agents()
        if not away:
            return super().get_user(doc)

        # "Based on Field" assignment rule assigns through the document field hence return back basic user pool
        if self.rule == "Weighted Distribution":
            user_pool_fieldname = "weighted_users"
        elif self.rule in ("Round Robin", "Load Balancing"):
            user_pool_fieldname = "users"
        else:
            return super().get_user(doc)

        # original set of users set inside the assignment rule
        assignment_rule_users = getattr(self, user_pool_fieldname)
        available_users = [u for u in assignment_rule_users if u.user not in away]

        # narrow the pool only if someone is still available; otherwise fall
        # back to the full list so an all-Away rule still assigns the ticket
        if available_users:
            setattr(self, user_pool_fieldname, available_users)

        # send filtered users to the core get_user method
        try:
            return super().get_user(doc)
        finally:
            # revert back to original users
            setattr(self, user_pool_fieldname, assignment_rule_users)
