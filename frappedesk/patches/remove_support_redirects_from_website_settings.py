import frappe


def execute():
	website_settings = frappe.get_doc("Website Settings")
	if website_settings.home_page in ["/", ""]:
		website_settings.home_page = "home"

	for route_redirect in website_settings.route_redirects:
		if route_redirect.source in ["/", ""] and route_redirect.target in [
			"support/kb",
			"/support/kb",
		]:
			website_settings.remove(route_redirect)

	website_settings.save()
