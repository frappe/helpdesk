# helpdesk/helpdesk/api/setup.py

import frappe

@frappe.whitelist(allow_guest=True)
def is_helpdesk_setup_complete():
    """
    Returns True if Helpdesk setup is complete
    """

    # Example logic:
    # Check if default department exists
    department_exists = frappe.db.exists("HD Department")

    # Check if default support email exists
    support_email = frappe.db.exists("HD Settings")

    if department_exists and support_email:
        return True

    return False
