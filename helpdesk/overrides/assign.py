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
        frappe.msgprint(
            msg=_("This agent is marked as Away "),
            title=_("Agent Unavailable"),
    )
        frappe.log_error("Ticket assigned to Away agent", "Agent Unavailable")




# removed user_query_condition
