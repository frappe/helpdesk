import frappe


def execute():
    portal_settings = frappe.get_single("Portal Settings")

    defaults = {
        "default_role": "HD Customer",
        "default_portal_home": "/helpdesk",
    }
    for field, value in defaults.items():
        if not portal_settings.get(field):
            portal_settings.set(field, value)

    portal_settings.save()
