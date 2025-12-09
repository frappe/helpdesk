import frappe


def execute():
    doctype = "HD Canned Response"
    canned_responses = frappe.get_all(doctype, pluck="name")

    for cr in canned_responses:
        canned_response = frappe.get_doc(doctype, cr)

        cr = frappe.get_doc(
            {
                "doctype": "HD Saved Reply",
                "title": canned_response.title,
                "response": canned_response.message,
                "scope": "Global",
            }
        ).insert(ignore_permissions=True)

        frappe.db.set_value("HD Saved Reply", cr.name, "owner", canned_response.owner)

    if not frappe.db.exists("DocType", doctype):
        return

    frappe.db.delete(doctype)
    frappe.delete_doc("DocType", doctype, force=True)
