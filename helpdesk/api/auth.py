import frappe

from helpdesk.utils import is_agent as _is_agent


@frappe.whitelist()
def get_user():
	current_user = frappe.session.user
	filters = {"name": current_user}
	fields = [
		"first_name",
		"full_name",
		"name",
		"user_image",
		"username",
	]
	user = frappe.get_value(
		doctype="User",
		filters=filters,
		fieldname=fields,
		as_dict=True,
	)

	is_agent = _is_agent()
	is_admin = user.username == "administrator"
	has_desk_access = is_agent or is_admin
	user_image = user.user_image
	user_first_name = user.first_name
	user_name = user.full_name
	user_id = user.name
	username = user.username

	return {
		"has_desk_access": has_desk_access,
		"is_admin": is_admin,
		"is_agent": is_agent,
		"user_id": user_id,
		"user_image": user_image,
		"user_first_name": user_first_name,
		"user_name": user_name,
		"username": username,
	}


@frappe.whitelist(allow_guest=True)
def oauth_providers():
	from frappe.utils.html_utils import get_icon_html
	from frappe.utils.oauth import get_oauth2_authorize_url, get_oauth_keys
	from frappe.utils.password import get_decrypted_password

	out = []
	providers = frappe.get_all(
		"Social Login Key",
		filters={"enable_social_login": 1},
		fields=["name", "client_id", "base_url", "provider_name", "icon"],
		order_by="name",
	)

	for provider in providers:
		client_secret = get_decrypted_password(
			"Social Login Key", provider.name, "client_secret"
		)
		if not client_secret:
			continue

		icon = None
		if provider.icon:
			if provider.provider_name == "Custom":
				icon = get_icon_html(provider.icon, small=True)
			else:
				icon = f"<img src='{provider.icon}' alt={provider.provider_name}>"

		if provider.client_id and provider.base_url and get_oauth_keys(provider.name):
			out.append(
				{
					"name": provider.name,
					"provider_name": provider.provider_name,
					"auth_url": get_oauth2_authorize_url(provider.name, "/helpdesk"),
					"icon": icon,
				}
			)

	return out
