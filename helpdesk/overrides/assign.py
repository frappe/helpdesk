import frappe
from frappe import _


def validate_agent_availability(doc, method=None):
    if not doc.allocated_to:
        return

    status = frappe.db.get_value(
        "HD Agent",
        {"user": doc.allocated_to},
        "availability_status",
    )

    if status == "Away":
        frappe.throw(
            _("This agent is marked as Away and cannot be assigned tickets."),
            title=_("Agent Unavailable"),
        )

def user_query_condition(user):
    return """
        EXISTS (
            SELECT 1 FROM `tabHD Agent`
            WHERE `tabHD Agent`.user = `tabUser`.name
            AND `tabHD Agent`.availability_status = 'Available'
        )
    """

