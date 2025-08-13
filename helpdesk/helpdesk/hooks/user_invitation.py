import frappe
from frappe.model.document import Document


def after_accept(invitation: Document, user: Document, user_inserted: bool) -> None:
    if not frappe.db.exists("HD Agent", {"user": user.email}):
        frappe.get_doc(
            doctype="HD Agent",
            user=user.email,
            agent_name=user.first_name,
            is_active=True,
        ).insert(True)
