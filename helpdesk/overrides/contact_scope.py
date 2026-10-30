import frappe
from helpdesk.api.dashboard import _locked_brand


def permission_query(user=None):
    """Care-team-only users see only contacts linked to Careverse tickets (and their own)."""
    user = user or frappe.session.user
    if user == "Administrator" or not _locked_brand(user):
        return ""
    u = frappe.db.escape(user)
    return (
        f"(`tabContact`.owner = {u} OR `tabContact`.user = {u} "
        "OR `tabContact`.name IN (SELECT contact FROM `tabHD Ticket` "
        "WHERE brand = 'Careverse' AND IFNULL(contact, '') != '') "
        "OR `tabContact`.name IN (SELECT ce.parent FROM `tabContact Email` ce "
        "WHERE ce.email_id IN (SELECT raised_by FROM `tabHD Ticket` WHERE brand = 'Careverse')))"
    )
