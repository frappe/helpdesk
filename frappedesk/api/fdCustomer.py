import frappe


@frappe.whitelist()
def get_contact(doctype, link_name):
    contacts = frappe.db.get_all(
        "Dynamic Link",
        fields=["parent", "link_title"],
        filters={"parenttype": doctype, "link_name": link_name},
    )
    contact_list = []

    for contact in contacts:
        contact_doc = frappe.get_doc("Contact", contact["parent"])

        contact_list.append(contact_doc)

    return contact_list
