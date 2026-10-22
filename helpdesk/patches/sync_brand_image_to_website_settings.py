import frappe

from helpdesk.helpdesk.doctype.hd_settings.helpers import get_brand_image


def execute():
    """Brand images uploaded before the sync never reached sign-in and invite emails."""
    if frappe.db.get_single_value("Website Settings", "app_logo"):
        return
    if brand_image := get_brand_image(frappe.get_single("HD Settings")):
        frappe.db.set_single_value("Website Settings", "app_logo", brand_image)
