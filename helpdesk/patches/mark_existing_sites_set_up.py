import frappe


def execute():
    """Sites that ran Helpdesk before the first-run setup existed skip it. A fresh install marks
    this patch done without running it, so only new sites see the setup."""
    frappe.db.set_single_value("HD Settings", "setup_complete", 1)
