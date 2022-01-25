from helpdesk.setup.install import set_home_page_to_kb
import frappe

def execute():
    remove_base_route_redirect()
    set_home_page_to_kb()

def remove_base_route_redirect():
    website_settings = frappe.get_doc("Website Settings")

    for route_redirect in website_settings.route_redirects:
        if(route_redirect.source == "/" and route_redirect.target == "/support/kb"):
            website_settings.remove('route_redirects', route_redirect)
            website_settings.save()
