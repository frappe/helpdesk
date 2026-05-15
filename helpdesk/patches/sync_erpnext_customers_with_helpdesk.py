import frappe

from helpdesk.integrations.erpnext.customer import sync_all_customers


def execute():
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

    # Add custom fields for syncing ERPNext customers with Helpdesk
    # hd_customer field in Customer doctpy
    frappe.db.set_single_value("ERPNext HD Settings", "enabled", 1)

    if "erpnext" not in frappe.get_installed_apps():
        return

    create_custom_fields(
        {
            "Customer": [
                {
                    "fieldname": "hd_customer",
                    "fieldtype": "Data",
                    "label": "HD Customer",
                    "read_only": 1,
                    "insert_after": "customer_name",
                }
            ]
        }
    )

    sync_all_customers()
