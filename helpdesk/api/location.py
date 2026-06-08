"""Location helpers — county / sub-county lookups and per-account remembering.

Story 354: County + Sub-County picker on ticket creation with auto-remember.
"""

import frappe
from frappe import _


@frappe.whitelist(allow_guest=True)
def get_counties() -> list[str]:
    """Return a sorted list of all Kenya counties from HD County."""
    rows = frappe.db.get_all(
        "HD County",
        fields=["county_name"],
        order_by="county_name asc",
    )
    return [r.county_name for r in rows if r.county_name]


@frappe.whitelist(allow_guest=True)
def get_sub_counties(county: str) -> list[dict]:
    """Return a sorted list of subcounties for the given county from HD Subcounty.

    Returns list of dicts with 'label' (display name) and 'value' (document name)
    so the form can display the readable name but save the correct document ID.
    """
    if not county:
        return []
    rows = frappe.db.get_all(
        "HD Subcounty",
        filters={"county": county},
        fields=["name", "subcounty_name"],
        order_by="subcounty_name asc",
    )
    return [
        {"label": r.subcounty_name, "value": r.name}
        for r in rows if r.subcounty_name
    ]


@frappe.whitelist()
def get_contact_location() -> dict:
    """Return the saved county + sub_county for the current session's HD Customer.

    Looks up the HD Customer linked to the current user's Contact record.
    Returns ``{"county": "...", "sub_county": "..."}`` or an empty dict.
    """
    user = frappe.session.user
    if not user or user == "Guest":
        return {}

    # Find contact by email
    contact_name = frappe.db.get_value("Contact", {"email_id": user})
    if not contact_name:
        return {}

    # Get customer linked to this contact
    from helpdesk.utils import get_customer

    customers = get_customer(contact_name)
    if not customers:
        return {}

    customer_name = customers[0]
    customer = frappe.db.get_value(
        "HD Customer",
        customer_name,
        ["county", "sub_county"],
        as_dict=True,
    )
    if not customer:
        return {}

    return {
        "county": customer.county or "",
        "sub_county": customer.sub_county or "",
    }
