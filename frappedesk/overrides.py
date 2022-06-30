import frappe
def pull_support_emails():
	if (frappe.db.exists("Email Account", "Support")):
		email_account = frappe.get_doc("Email Account", "Support")
		
		if email_account.enable_incoming:
			email_account.receive()

def on_assignment_rule_trash(doc, event):
	if not frappe.get_all("Assignment Rule", filters={"document_type": "Ticket", "name": ["!=", doc.name]}):
		frappe.throw("There should atleast be 1 assignment rule for ticket")