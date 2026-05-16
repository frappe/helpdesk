import frappe

from helpdesk.integrations.erpnext.customer import (
    create_customer_field,
    sync_hd_erpnext_customers,
)


def execute():
    create_customer_field()
    # TODO: do this or not in patch or should it be opt in?
    frappe.set_single_value("ERPNext HD Settings", "enabled", 1)
    sync_hd_erpnext_customers()
