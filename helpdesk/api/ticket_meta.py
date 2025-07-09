import frappe


@frappe.whitelist()
def get_fields_meta(doctype="HD Ticket", fieldtypes=None):
    """
    Returns the metadata for the given doctype.
    """

    all_fields = frappe.get_meta(doctype).fields
    fields = []
    for field in all_fields:
        if field.fieldtype in fieldtypes:
            fields.append(field)
    return fields
