import frappe

"""
	Signup for customer portal only (TODO: agent signups)
"""
@frappe.whitelist(allow_guest=True)
def signup(email, first_name, last_name):
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
			"send_welcome_email": "0"
			# "role_profile_name": "Frappedesk Contact"	TODO: add this role profile and then un-comment this part
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

@frappe.whitelist(allow_guest=True)
def verify_and_create_account(request_key, email, password):
	account_request = frappe.get_doc("Desk Account Request", {"email": email})
	if (account_request):
		if (account_request.request_key == request_key):
			current_user = frappe.session.user
			frappe.set_user("Administrator")
			
			user = frappe.get_doc("User", account_request.user)
			user.new_password = password
			user.save()

			frappe.set_user(current_user)
		else:
			frappe.throw("Ivalid request key")
	else:
		frappe.throw(f"Account request for {email} not found, please signup first")