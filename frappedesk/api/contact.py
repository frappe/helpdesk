from dataclasses import field
import frappe

def get_all():
    all_contacts = frappe.get_all("Contact", fields=["*"])
    return all_contacts
