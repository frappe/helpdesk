from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    create_custom_fields(get_custom_fields())


def get_custom_fields():
    return {
        "Communication": [
            {
                "default": "0",
                "fieldname": "is_auto_generated",
                "fieldtype": "Check",
                "label": "Is Auto Generated",
                "insert_after": "read_by_recipient_on",
                "read_only": 1,
            }
        ]
    }
