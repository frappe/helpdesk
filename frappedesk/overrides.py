import frappe


def pull_support_emails():
	email_accounts = frappe.get_all(
		"Email Account",
		filters=[["IMAP Folder", "append_to", "=", "Ticket"]],
		fields=["name"],
	)
	for account in email_accounts:
		email_account = frappe.get_doc("Email Account", account["name"])

		if email_account.enable_incoming:
			email_account.receive()


def on_assignment_rule_trash(doc, event):
	if not frappe.get_all(
		"Assignment Rule", filters={"document_type": "Ticket", "name": ["!=", doc.name]}
	):
		frappe.throw("There should atleast be 1 assignment rule for ticket")
