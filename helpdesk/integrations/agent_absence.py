import frappe
from frappe import _
from frappe.utils import add_days, getdate, nowdate


def validate(doc, method=None):
    """Validation for HD Agent Absence."""
    if not doc.days or doc.days < 1:
        frappe.throw(_("Number of days must be at least 1."))
    if doc.days > 365:
        frappe.throw(_("Number of days can't be more than 365."))
    if not frappe.db.exists("HD Agent", doc.user):
        frappe.throw(_("{0} is not a Helpdesk agent.").format(doc.user))
    if doc.is_new() and getdate(doc.from_date) < getdate(nowdate()):
        frappe.throw(_("The start date can't be in the past."))

    doc.return_date = add_days(getdate(doc.from_date), doc.days)

    if not doc.cancelled:
        clash = frappe.db.exists("HD Agent Absence", {
            "user": doc.user, "cancelled": 0, "name": ["!=", doc.name or ""],
            "from_date": ["<", doc.return_date], "return_date": [">", doc.from_date]})
        if clash:
            frappe.throw(_("{0} already has an absence that overlaps these dates ({1}).")
                         .format(doc.user, clash))
