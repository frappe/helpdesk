import frappe


def should_sync():
    return "erpnext" in frappe.get_installed_apps() and frappe.db.get_single_value(
        "ERPNext HD Settings", "enabled"
    )


def set_links(erpnext_customer_name: str, hd_customer_name: str):
    frappe.db.set_value(
        "HD Customer",
        hd_customer_name,
        "erpnext_customer",
        erpnext_customer_name,
        update_modified=False,
    )
    frappe.db.set_value(
        "Customer",
        erpnext_customer_name,
        "hd_customer",
        hd_customer_name,
        update_modified=False,
    )


def create_customer_field():
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

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
                    "hidden": 1,
                }
            ]
        }
    )
