import frappe


def execute():
    doctype = "HD Canned Response"
    canned_responses = frappe.get_all(doctype)
    for cr in canned_responses:
        canned_response = frappe.get_doc(doctype, cr.name)
        frappe.get_doc(
            {
                "doctype": "Email Template",
                "__newname": canned_response.title,
                "subject": canned_response.title,
                "response": canned_response.message,
                "reference_doctype": "HD Ticket",
            }
        ).insert(ignore_permissions=True)

    if not frappe.db.exists("DocType", doctype):
        return

    frappe.db.delete(doctype)
    frappe.delete_doc("DocType", doctype, force=True)
