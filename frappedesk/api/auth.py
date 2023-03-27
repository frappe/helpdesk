import frappe


@frappe.whitelist()
def get_user():
	user = frappe.get_doc("User", frappe.session.user)

	is_agent = bool(frappe.db.exists("HD Agent", frappe.session.user))
	is_admin = user.username == "administrator"
	has_desk_access = is_agent or is_admin
	user_image = user.user_image
	user_name = user.full_name
	user_id = user.name
	username = user.username

	return {
		"has_desk_access": has_desk_access,
		"is_admin": is_admin,
		"is_agent": is_agent,
		"user_id": user_id,
		"user_image": user_image,
		"user_name": user_name,
		"username": username,
	}
