import frappe
from frappe.model.document import Document

from helpdesk.api.contact import create_contact


@frappe.whitelist()
def create_customer(customer: dict, primary_contact: dict | None = None) -> str:
    """Create an HD Customer and optionally invite a primary contact.

    The primary contact is created, invited by email and set as the customer's
    primary contact in a single operation.
    """
    frappe.has_permission("HD Customer", "create", throw=True)

    customer_doc = frappe.get_doc(
        {
            "doctype": "HD Customer",
            "customer_name": customer.get("customer_name"),
            "customer_type": customer.get("customer_type"),
            "domain": customer.get("domain"),
            "image": customer.get("image"),
            "country": customer.get("country"),
        }
    )
    customer_doc.insert()

    if primary_contact and primary_contact.get("email"):
        add_primary_contact(customer_doc, primary_contact)

    return customer_doc.name


def add_primary_contact(customer_doc: Document, primary_contact: dict) -> None:
    contact_name = create_contact(
        {
            "first_name": primary_contact.get("first_name"),
            "last_name": primary_contact.get("last_name"),
            "email": primary_contact.get("email"),
            "phone": primary_contact.get("mobile_no"),
            "customer": customer_doc.name,
        },
        invite=True,
    )
    customer_doc.append("contacts", {"contact_name": contact_name, "is_manager": True})
    customer_doc.primary_contact = contact_name
    customer_doc.save()
