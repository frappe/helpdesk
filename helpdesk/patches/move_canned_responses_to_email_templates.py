import frappe


def execute():
    doctype = "HD Canned Response"
    canned_responses = frappe.get_all(doctype, pluck="name")

    name_counts = {}

    for cr in canned_responses:
        canned_response = frappe.get_doc(doctype, cr)

        if canned_response.title in name_counts:
            name_counts[canned_response.title] += 1
        else:
            name_counts[canned_response.title] = 1

        if name_counts[canned_response.title] == 1:
            template_name = canned_response.title
        else:
            template_name = (
                f"{canned_response.title} {name_counts[canned_response.title]}"
            )

        frappe.get_doc(
            {
                "doctype": "Email Template",
                "name": template_name,
                "subject": canned_response.title,
                "response": canned_response.message,
                "reference_doctype": "HD Ticket",
                "owner": canned_response.owner,
            }
        ).insert(ignore_permissions=True)

    if not frappe.db.exists("DocType", doctype):
        return

    frappe.db.delete(doctype)
    frappe.delete_doc("DocType", doctype, force=True)
