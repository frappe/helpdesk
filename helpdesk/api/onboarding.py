import frappe
from frappe.utils import add_days, get_datetime, now_datetime

# Hide the onboarding popup once user is familiar with product
ONBOARDING_TICKET_THRESHOLD = 100
ONBOARDING_AGE_DAYS = 30


@frappe.whitelist()
def should_show_onboarding() -> bool:
    """
    Decide whether the onboarding banner + auto-popup should still be shown.

    Returns False when:
      - there are more than ``ONBOARDING_TICKET_THRESHOLD`` tickets, or
      - the current user's account is older than ``ONBOARDING_AGE_DAYS`` days.

    Step completion is already tracked on the client via
    ``useOnboarding("helpdesk").isOnboardingStepsCompleted``, so it's not
    re-checked here.
    """
    ticket_count = frappe.db.count("HD Ticket")
    if ticket_count > ONBOARDING_TICKET_THRESHOLD:
        return False

    user_creation = frappe.db.get_value("User", frappe.session.user, "creation")
    if user_creation and get_datetime(user_creation) < add_days(
        now_datetime(), -ONBOARDING_AGE_DAYS
    ):
        return False

    return True


@frappe.whitelist()
def get_first_ticket():
    """Get first ticket created except the default ticket"""
    ticket = frappe.get_all(
        "HD Ticket",
        filters={
            "subject": ["!=", "Welcome to Helpdesk"],
            "owner": ["=", frappe.session.user],
        },
        fields=["name"],
        order_by="creation asc",
        limit=1,
    )
    return ticket[0].name if ticket else None


@frappe.whitelist()
def get_general_category_id():
    """Get the id of the general category"""
    category = frappe.get_all(
        "HD Article Category",
        filters={"category_name": ["=", "General"]},
        pluck="name",
        order_by="creation asc",
        limit=1,
    )
    return category[0] if category else None
