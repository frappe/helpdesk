import frappe


@frappe.whitelist()
def update_helpdesk_name(name):
    doc = frappe.get_doc("Frappe Desk Settings")
    doc.helpdesk_name = name
    doc.save(ignore_permissions=True)

    return doc.helpdesk_name


@frappe.whitelist()
def skip_helpdesk_name_setup():
    doc = frappe.get_doc("Frappe Desk Settings")
    doc.initial_helpdesk_name_setup_skipped = True
    doc.save(ignore_permissions=True)

    return doc
