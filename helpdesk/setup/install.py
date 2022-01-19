import frappe

def initial_setup():
    # TODO: add temp catagories and articles for fillers
    add_base_route_redirect_to_website_settings()

def add_base_route_redirect_to_website_settings():
    website_settings = frappe.get_doc("Website Settings")
    
    for route_redirects in website_settings.route_redirects:
        if(route_redirects.source == "/" or route_redirects.source == ""):
            return

    base_route = frappe.get_doc({
        "doctype": "Website Route Redirect",
        "source": "/" ,
        "target": "/support/kb"
    })

    website_settings.append('route_redirects', base_route)
    website_settings.save()