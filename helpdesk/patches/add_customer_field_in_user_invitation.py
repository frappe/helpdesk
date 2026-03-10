from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    create_custom_fields(get_custom_fields())


def get_custom_fields():
    return {
        "User Invitation": [
            {
                "fieldname": "customer",
                "label": "Customer",
                "fieldtype": "Link",
                "options": "HD Customer",
                "insert_after": "roles",
            }
        ],
    }
