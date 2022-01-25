import frappe

def before_install():
    set_home_page_to_kb()

def after_install():
    add_default_categories()

def set_home_page_to_kb():
    website_settings = frappe.get_doc("Website Settings")

    if not website_settings.home_page:
        website_settings.home_page = '/support/kb'
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