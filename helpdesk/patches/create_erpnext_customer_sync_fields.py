import frappe


# Patch to create the `hd_customer` custom field on ERPNext Customer, and to sync HD Customer of Helpdesk to Customer of ERPNext.
def execute():
    if "erpnext" not in frappe.get_installed_apps():
        return

    from helpdesk.helpdesk.integrations.erpnext.customer import (
        setup_erpnext_customer_sync,
    )

    setup_erpnext_customer_sync()
