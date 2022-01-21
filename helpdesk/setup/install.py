import frappe

def before_install():
    add_base_route_redirect_to_website_settings()

def after_install():
    add_default_categories()

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

def add_default_categories():
    frappe.get_doc({
        "doctype": "Category",
        "category_name": "FAQ",
        "description": "Description for your FAQs",
        "is_group": True
    }).insert()

    frappe.get_doc({
        "doctype": "Category",
        "category_name": "Getting Started",
        "description": "Description for your Getting Started",
        "is_group": True
    }).insert()