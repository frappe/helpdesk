import frappe

from helpdesk.utils import agent_manager_only


@frappe.whitelist(methods=["POST"])
@agent_manager_only
def mark_persona_captured(brand_name: str | None = None) -> None:
    """Flag the onboarding persona questionnaire as done so it never re-prompts,
    and adopt the org name as the brand name in two places: the Helpdesk portal
    brand (HD Settings) and the site-wide app name (Website Settings), which
    otherwise falls back to "Frappe" across the desk, PWA and app identity.

    Direct single-value writes, mirroring the customer portal notice: they skip
    each doctype's document lifecycle (validate/on_update) so an unrelated
    invalid setting can't block finishing onboarding.
    """
    frappe.db.set_single_value("HD Settings", "persona_captured", 1)
    brand_name = (brand_name or "").strip()
    if brand_name:
        frappe.db.set_single_value("HD Settings", "brand_name", brand_name)
        frappe.db.set_single_value("Website Settings", "app_name", brand_name)
        # set_single_value skips Website Settings' on_update, so clear the cache
        # ourselves for the new brand to show up in the desk/PWA/app identity.
        frappe.clear_cache()


@frappe.whitelist()
def get_first_ticket(ticket: str | None = None):
    """Get first ticket created except the default ticket"""
    # If a cached ticket ID was passed, verify it still exists
    if ticket and frappe.db.exists("HD Ticket", ticket):
        return ticket

    result = frappe.get_all(
        "HD Ticket",
        filters={
            "subject": ["!=", "Welcome to Helpdesk"],
            "owner": ["=", frappe.session.user],
        },
        fields=["name"],
        order_by="creation asc",
        limit=1,
    )
    return result[0].name if result else None


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
