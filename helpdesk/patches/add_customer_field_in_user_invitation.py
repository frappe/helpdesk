from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    create_custom_fields(get_custom_fields())


def get_custom_fields():
    return {
        "User Invitation": [
            {
                "fieldname": "contact",
                "label": "Contact",
                "fieldtype": "Link",
                "options": "Contact",
                "insert_after": "roles",
                "set_only_once": 1,
            },
            {
                "fieldname": "customer",
                "label": "Customer",
                "fieldtype": "Link",
                "options": "HD Customer",
                "insert_after": "contact",
                "set_only_once": 1,
            },
        ],
    }
