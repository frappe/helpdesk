"""
Ensures every ticket about "Report" or "Registration" issues goes directly
and exclusively to a dedicated agent, regardless of which region/team the
ticket would otherwise round-robin to, and regardless of whether the
implementer picked the correct ticket type when raising it.

Matching is by ticket_type first, then falls back to word-boundary keyword
matching on subject/description (not plain substring — avoids false
positives like "transport" matching "report").
"""

import re

import frappe
from frappe.desk.form.assign_to import add as assign_to_add
from frappe.desk.form.assign_to import clear as clear_assignments

DEDICATED_AGENT = "siranjofu@tiberbu.com"
DEDICATED_TYPES = {"Report", "Registration"}

# Word-boundary matches only — "report" won't match inside "transport".
_KEYWORD_RE = re.compile(r"\b(report|regist\w*)\b", re.IGNORECASE)


def route_report_registration_tickets(doc, method=None):
    # Exact ticket_type match only -- the keyword fallback matched "report"/
    # "regist..." anywhere in subject/description and was sweeping up Bug
    # Report, Complaint, Technical Support and other unrelated tickets.
    if doc.get("ticket_type") not in DEDICATED_TYPES:
        return

    ticket_name = str(doc.name)

    try:
        clear_assignments("HD Ticket", ticket_name, ignore_permissions=True)
    except Exception:
        frappe.log_error(
            title=f"Report/Registration routing: clear assignment failed for {ticket_name}",
            message=frappe.get_traceback(),
        )

    try:
        assign_to_add({
            "assign_to": [DEDICATED_AGENT],
            "doctype": "HD Ticket",
            "name": ticket_name,
        })
    except Exception:
        frappe.log_error(
            title=f"Report/Registration routing: assign failed for {ticket_name}",
            message=frappe.get_traceback(),
        )
