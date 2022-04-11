import frappe

"""
	Singup for customer portal only (TODO: agent signups)
"""
@frappe.whitelist(allow_guest=True)
def signup(email, first_name, last_name, password):
	frappe.utils.validate_email_address(email, True)

	current_user = frappe.session.user
	frappe.set_user("Administrator")

	email = email.strip().lower()

	if not frappe.db.exists("User", email):
		user = frappe.get_doc({
			"doctype": "User",
			"email": email,
			"first_name": first_name,
			"last_name": last_name,
			"new_password": password,
			"send_welcome_email": "0"
			# "role_profile_name": "Helpdesk Contact"	TODO: add this role profile and then un-comment this part
		}).insert()

		frappe.get_doc({
			"doctype": "Desk Account Request",
			"email": email,
			"user": user.name,
		}).insert()

		frappe.set_user(current_user)
	else:
		frappe.set_user(current_user)
		frappe.throw("User already exists, please try loggin in using this email")
	