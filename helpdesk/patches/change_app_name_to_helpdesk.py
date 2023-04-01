import frappe
from frappe.installer import add_to_installed_apps, remove_from_installed_apps


def execute():
    old_app_name = "frappedesk"
    new_app_name = "helpdesk"
    installed_apps = frappe.db.get_global("installed_apps")
    
    if old_app_name in installed_apps:
        remove_from_installed_apps(old_app_name)
        add_to_installed_apps(new_app_name)
