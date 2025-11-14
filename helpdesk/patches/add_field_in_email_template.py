from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from helpdesk.setup.install import get_custom_fields_for_canned_responses


def execute():
    create_custom_fields(get_custom_fields_for_canned_responses())
