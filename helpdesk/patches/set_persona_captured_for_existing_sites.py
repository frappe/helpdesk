import frappe


def execute():
    # Existing sites are already set up by upgrade time; skip onboarding for them.
    # Every site ships one welcome ticket, so >1 means real usage — a site with
    # only that welcome ticket is effectively fresh and still sees the questionnaire.
    if frappe.db.count("HD Ticket") > 1:
        frappe.db.set_single_value("HD Settings", "persona_captured", 1)
