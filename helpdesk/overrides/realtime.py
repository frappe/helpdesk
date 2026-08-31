import frappe
from frappe.realtime import has_permission as frappe_has_permission

from helpdesk.utils import is_agent


@frappe.whitelist()
def has_permission(doctype: str, name: str, ptype: str = "read") -> bool:
    """Socket room-join gate (doc_subscribe / doc_open / doctype_subscribe).

    HD Ticket rooms carry internal payloads (docinfo_update), so they are
    agent-only even though customers can read their own tickets. Delegation
    keeps team-based ticket restrictions for agents.
    """
    if doctype == "HD Ticket" and not is_agent():
        return False
    return frappe_has_permission(doctype, name, ptype)
