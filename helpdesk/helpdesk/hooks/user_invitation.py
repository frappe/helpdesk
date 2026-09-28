import frappe
from frappe.core.doctype.user.user import create_contact
from frappe.model.document import Document


def after_accept(invitation: Document, user: Document, user_inserted: bool) -> None:
    agent_roles = {"Agent", "Agent Manager", "System Manager"}
    customer_roles = {"HD Customer", "HD Customer Manager"}
    invited_roles = {d.role for d in invitation.roles}

    if invited_roles & agent_roles:  # Intersection of invited roles and agent roles
        create_agent(user)

    if invited_roles & customer_roles:
        contact = get_or_create_contact(invitation, user)
        attach_image(user, contact)
        link_to_customer(
            invitation.customer,
            contact,
            is_manager="HD Customer Manager" in invited_roles,
        )


def get_or_create_contact(invitation: Document, user: Document) -> str | None:
    """Resolve the contact for an accepted invite, reusing the one chosen at
    invite time to avoid creating a duplicate."""
    if invitation.contact and frappe.db.exists("Contact", invitation.contact):
        if not frappe.db.get_value("Contact", invitation.contact, "user"):
            frappe.db.set_value("Contact", invitation.contact, "user", user.name)
        return invitation.contact

    create_contact(user)
    return frappe.db.get_value(
        "Contact", {"user": user.name}, "name"
    ) or frappe.db.get_value("Contact", {"email_id": user.name}, "name")


def create_agent(user: Document) -> None:
    if not frappe.db.exists("HD Agent", {"user": user.email}):
        frappe.get_doc(
            doctype="HD Agent",
            user=user.email,
            agent_name=user.first_name,
            is_active=True,
        ).insert(True)


def attach_image(user: Document, contact: str | None) -> None:
    if not user.user_image or not contact:
        return
    frappe.db.set_value("Contact", contact, "image", user.user_image)


def link_to_customer(
    customer: str, contact: str | None, is_manager: bool = False
) -> None:
    if not customer or not contact:
        return
    if not frappe.db.exists("HD Customer", customer):
        return

    doc = frappe.get_doc("HD Customer", customer)
    for row in doc.contacts:
        if row.contact_name == contact:
            if is_manager and not row.is_manager:
                row.is_manager = True
                doc.save(ignore_permissions=True)
            return
    doc.append("contacts", {"contact_name": contact, "is_manager": is_manager})
    doc.save(ignore_permissions=True)
