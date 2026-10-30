"""
Dedup wrapper for Frappe's core Assignment Rule apply().

HD Ticket's own creation flow saves the document multiple times in quick
succession (SLA/priority setup, etc. right after insert). Since
assignment_rule.apply() was hooked on both after_insert and on_update, each
of those internal saves re-ran assignment logic and re-sent the assignment
notification email -- flooding the same recipient with several identical
copies within seconds of a single new ticket. This wraps the real apply()
with a short per-ticket cache guard so repeat saves in that burst are
suppressed, while a genuine later reassignment (outside the window) still
runs normally.
"""
import frappe
from frappe.automation.doctype.assignment_rule.assignment_rule import apply as _apply

DEDUP_WINDOW_SECONDS = 15


def apply_once(doc, method=None):
    if doc.doctype != "HD Ticket":
        return _apply(doc, method=method)

    cache_key = f"hd_ticket_assignment_rule_applied:{doc.name}"
    if frappe.cache().get_value(cache_key):
        return
    frappe.cache().set_value(cache_key, 1, expires_in_sec=DEDUP_WINDOW_SECONDS)

    return _apply(doc, method=method)
