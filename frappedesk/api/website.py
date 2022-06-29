import frappe

@frappe.whitelist(allow_guest=True)
def brand_html():
    settings_doc = frappe.get_doc("Website Settings")
    if settings_doc.brand_html:
        return settings_doc.brand_html
    else:
        if (settings_doc.banner_image):
            return f"<img src='{settings_doc.banner_image}' style='max-width: 80px; margin-top: -5px'>"
        else:
            return ""

@frappe.whitelist(allow_guest=True)
def navbar_items():
    return frappe.get_doc("Website Settings").top_bar_items

@frappe.whitelist(allow_guest=True)
def company_name():
    name = frappe.get_doc("Company").company_name
    return name if name else ''