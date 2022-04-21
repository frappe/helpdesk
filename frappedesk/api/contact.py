from dataclasses import field
import frappe

@frappe.whitelist(allow_guest=True)
def get_all():
    all_contacts = frappe.get_all("Contact", fields=["*"])
    return all_contacts
