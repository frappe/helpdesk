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

        Filter out away agents from nomal users present in the assignment rule

        if all agents are on away status resort to the normal pool of users

        """

        away = get_away_agents()
        if not away:
            return super().get_user(doc)

        original_users = self.users
        original_weighted = self.weighted_users

        available_users = [u for u in original_users if u.user not in away]
        available_weighted = [u for u in original_weighted if u.user not in away]

        # narrow the pool only if someone is still available; otherwise fall
        # back to the full list so an all-Away rule still assigns the ticket
        if available_users:
            self.users = available_users
        if available_weighted:
            self.weighted_users = available_weighted

        # send filtered users to the core get_user method
        try:
            return super().get_user(doc)

        except Exception as e:
            frappe.throw(str(e))

        # revert back to original users
        finally:
            self.users = original_users
            self.weighted_users = original_weighted
