import frappe
from frappe.automation.doctype.assignment_rule.assignment_rule import AssignmentRule


def get_agents_by_availability(availability: str) -> set[str]:
    """User ids of HD Agents currently marked with the given availability."""
    return set(
        frappe.get_all(
            "HD Agent",
            filters={"availability": availability},
            pluck="user",
        )
    )


class HelpdeskAssignmentRule(AssignmentRule):
    def get_user(self, doc):
        """
        Override get_user method from framework.
        always Active agents are preferred; fall back to Busy if no Active is available;
        fall back to the full pool (including Away) only if no one else
        is available, so the ticket is never left unassigned.
        """

        away = get_agents_by_availability("Away")
        busy = get_agents_by_availability("Busy")
        if not away and not busy:
            return super().get_user(doc)

        # "Based on Field" assigns through the document field, so the
        # availability filter does not apply.
        if self.rule == "Weighted Distribution":
            user_pool_fieldname = "weighted_users"
        elif self.rule in ("Round Robin", "Load Balancing"):
            user_pool_fieldname = "users"
        else:
            return super().get_user(doc)

        original_pool = getattr(self, user_pool_fieldname)
        active_only = [
            u for u in original_pool if u.user not in away and u.user not in busy
        ]
        not_away = [u for u in original_pool if u.user not in away]

        # Tier: Active → Busy → full pool (Away as last resort)
        if active_only:
            preferred_pool = active_only
        elif not_away:
            preferred_pool = not_away
        else:
            preferred_pool = original_pool

        setattr(self, user_pool_fieldname, preferred_pool)
        try:
            return super().get_user(doc)
        finally:
            setattr(self, user_pool_fieldname, original_pool)
