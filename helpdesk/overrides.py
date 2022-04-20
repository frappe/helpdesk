import frappe
def pull_support_emails():
    if (frappe.db.exists("Email Account", "Support")):
        email_account = frappe.get_doc("Email Account", "Support")
        
        if email_account.enable_incoming:
            email_account.receive()