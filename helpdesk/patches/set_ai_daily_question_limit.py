import frappe


def execute():
    """A new Int field on a Single starts empty, which would leave every visitor at a limit of 0."""
    if not frappe.db.get_single_value("HD Settings", "ai_daily_question_limit"):
        frappe.db.set_single_value("HD Settings", "ai_daily_question_limit", 20)
