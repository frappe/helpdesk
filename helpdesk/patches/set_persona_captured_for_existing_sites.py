import frappe


def execute():
    # Existing sites are already set up by upgrade time; skip onboarding for them.
    # Fresh installs have no tickets yet, so they still see the questionnaire.
    if frappe.db.count("HD Ticket"):
        frappe.db.set_single_value("HD Settings", "persona_captured", 1)
