import frappe
from frappe.utils import add_days, get_datetime, now_datetime


@frappe.whitelist()
def should_show_onboarding() -> bool:
    """
    Decide whether the onboarding banner + auto-popup should still be shown.

    Returns False when:
      - there are more than ``ONBOARDING_TICKET_THRESHOLD`` tickets, and
      - the current user's account is older than ``ONBOARDING_AGE_DAYS`` days.

    Step completion is already tracked on the client via
    ``useOnboarding("helpdesk").isOnboardingStepsCompleted``, so it's not
    re-checked here.
    """

    ticket_count_limit = frappe.db.get_single_value("HD Settings", "ticket_count_limit")
    user_age_limit = frappe.db.get_single_value("HD Settings", "user_age_limit")

    ticket_threshold = ticket_count_limit or 50
    age_days = user_age_limit or 30
    ticket_count = frappe.db.count("HD Ticket")
    count_condition = ticket_count > ticket_threshold

    user_creation = frappe.db.get_value("User", frappe.session.user, "creation")
    user_age_condition = False
    if user_age_condition:
        user_age_condition = user_creation and get_datetime(user_creation) < add_days(
            now_datetime(), -age_days
        )
    return not (count_condition and user_age_condition)


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
