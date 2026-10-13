import frappe

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
    frappe.has_permission(doctype, ptype, doc=name, throw=True)
    return True


@frappe.whitelist()
def can_subscribe_doc(doctype: str, docname: str) -> bool:
    """Frappe v15 socket server calls this instead of has_permission."""
    return has_permission(doctype, docname)
