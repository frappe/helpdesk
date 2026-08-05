import frappe
from frappe.model.document import Document

from helpdesk.api.contact import create_contact


@frappe.whitelist()
def create_customer(customer: dict, primary_contact: dict | None = None) -> dict:
    """Create an HD Customer and optionally invite a primary contact.

    The primary contact is created, invited by email and set as the customer's
    primary contact in a single operation. Returns the customer name and the
    emails an invitation was sent to.
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

    invited_emails: list[str] = []
    if primary_contact and primary_contact.get("email"):
        invited_emails = add_primary_contact(customer_doc, primary_contact)

    return {"name": customer_doc.name, "invited_emails": invited_emails}


def add_primary_contact(customer_doc: Document, primary_contact: dict) -> list[str]:
    """Set the primary contact, reusing an existing contact for the email.

    The contact is created first when the email is unknown, so the form's
    name and phone are kept; add_contacts then adds it directly if it has a
    linked user and invites it by email otherwise.
    """
    email = primary_contact.get("email")
    contact_name = frappe.db.get_value("Contact", {"email_id": email}, "name")
    if not contact_name:
        contact_name = create_contact(
            {
                "first_name": primary_contact.get("first_name"),
                "last_name": primary_contact.get("last_name"),
                "email": email,
                "phone": primary_contact.get("mobile_no"),
            }
        )
    result = customer_doc.add_contacts([contact_name], "HD Customer Manager")
    customer_doc.set_primary(contact_name)
    customer_doc.save()
    return result["invite_result"]["invited_emails"]


@frappe.whitelist()
def delete_customer(name: str, delete_tickets: bool = False) -> None:
    """Delete an HD Customer, either deleting or unlinking its tickets.

    When ``delete_tickets`` is set, every ticket linked to the customer is
    deleted as well. Otherwise the ``customer`` link on those tickets is cleared
    so the tickets are preserved but no longer tied to the deleted customer.
    """
    frappe.has_permission("HD Customer", "delete", throw=True)
    permission = "delete" if delete_tickets else "write"
    frappe.has_permission("HD Ticket", permission, throw=True)
    frappe.delete_doc("HD Customer", name, flags={"delete_tickets": delete_tickets})
