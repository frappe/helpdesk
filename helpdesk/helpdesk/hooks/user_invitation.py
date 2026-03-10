import frappe
from frappe.core.doctype.user.user import create_contact
from frappe.model.document import Document


def after_accept(invitation: Document, user: Document, user_inserted: bool) -> None:
    agent_roles = ["Agent", "Agent Manager", "System Manager"]
    customer_roles = ["HD Customer", "HD Customer Manager"]
    invited_roles = [d.role for d in invitation.roles]

    for role in invited_roles:
        if role in agent_roles:
            create_agent(user)
        elif role in customer_roles:
            create_contact(user)
            link_to_customer(user, invitation.customer)


def create_agent(user: Document) -> None:
    if not frappe.db.exists("HD Agent", {"user": user.email}):
        frappe.get_doc(
            doctype="HD Agent",
            user=user.email,
            agent_name=user.first_name,
            is_active=True,
        ).insert(True)


def link_to_customer(user: Document, customer: str) -> None:
    if not customer:
        return
    if not frappe.db.exists("HD Customer", customer):
        return

    contact = frappe.db.get_value(
        "Contact", {"user": user.name, "email_id": user.name}, "name"
    )
    if not contact:
        return

    doc = frappe.get_doc("HD Customer", customer)
    doc.append("contacts", {"contact_name": contact})
    frappe.flags.ignore_customer_role = True
    doc.save(ignore_permissions=True)
