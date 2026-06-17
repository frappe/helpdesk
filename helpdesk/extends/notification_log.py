import frappe


def before_insert(doc, method=None):
    if (
        doc.type == "Assignment"
        and doc.document_type == "HD Ticket"
        and doc.document_name
    ):
        doc.link = frappe.utils.get_url("/helpdesk/tickets/" + str(doc.document_name))
