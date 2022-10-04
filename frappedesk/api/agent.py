import frappe


def get_session_agent():
	session_user = frappe.session.user
	session_agent = None
	if session_user and frappe.db.exists("Agent", session_user):
		session_agent = frappe.get_doc("Agent", session_user)
		session_agent = session_agent.__dict__
		session_agent["image"] = frappe.get_value("User", session_user, "user_image")
	return session_agent


@frappe.whitelist()
def get_user():
	session_user = frappe.session.user
	session_agent = get_session_agent()
	username = frappe.get_value("User", frappe.session.user, "username")
	is_admin = username == "administrator"
	return {
		"agent": session_agent,
		"profile_image": frappe.get_value("User", session_user, "user_image"),
		"username": username,
		"isAdmin": is_admin,
		"user": session_user,
		"doc": frappe.get_doc("User", session_user),
		"has_desk_access": (session_agent or is_admin),
	}


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

		frappe.get_doc({"doctype": "Agent", "user": user.name}).insert()
	return
