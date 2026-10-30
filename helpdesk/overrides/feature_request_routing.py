"""
Feature Request tickets are worked by whoever the normal assignment process
gives them to (regional round-robin, same as any other ticket) — this only
links them into the currently active sprint automatically, so the Scrum
Master can track progress by filtering the Tickets list by Sprint, without
needing to be the assignee themselves.
"""

import frappe


def route_feature_requests(doc, method=None):
    if doc.get("ticket_type") != "Feature Request":
        return

    active_sprint = frappe.db.get_value("HD Sprint", {"status": "Active"}, "name")
    if active_sprint:
        frappe.db.set_value("HD Ticket", str(doc.name), "sprint", active_sprint)
        try:
            from helpdesk.integrations.zenhub import queue_ticket
            queue_ticket(str(doc.name))
        except Exception:
            frappe.log_error(title="ZenHub queue failed")  # never block ticket creation

def route_changed_to_feature_request(doc, method=None):
    if doc.get("ticket_type") != "Feature Request":
        return
    if doc.flags.in_insert or not doc.has_value_changed("ticket_type"):
        return
    route_feature_requests(doc)