import frappe

@frappe.whitelist(allow_guest=True)
def update_helpdesk_name(name):
    doc = frappe.get_doc("Frappe Desk Settings")
    doc.helpdesk_name = name
    doc.save(ignore_permissions=True)

    return doc.helpdesk_name
