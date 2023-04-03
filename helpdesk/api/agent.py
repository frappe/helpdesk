import frappe


@frappe.whitelist()
def sent_invites(emails, send_welcome_mail_to_user=True):
	for email in emails:
		if frappe.db.exists("User", email):
			user = frappe.get_doc("User", email)
		else:
			user = frappe.get_doc(
				{"doctype": "User", "email": email, "first_name": email.split("@")[0]}
			).insert()

			if send_welcome_mail_to_user:
				user.send_welcome_mail_to_user()

		frappe.get_doc({"doctype": "HD Agent", "user": user.name}).insert()
	return
