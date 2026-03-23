import frappe
from helpdesk.setup.default_views import add_default_views


def execute():
    # Delete all standard views
    frappe.db.delete("HD View", {"is_standard": 1})

    # Re-add default views
    add_default_views(for_existing_sites=True)
