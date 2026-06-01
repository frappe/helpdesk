import frappe
from frappe.model.document import Document

from helpdesk.integrations.erpnext.utils import (
    cascade_rename,
    in_cascade,
    set_links,
    should_sync,
    validate_rename_conflict,
)


def after_insert(doc: Document, method: str | None = None):
    if not should_sync() or doc.flags.get("ignore_erpnext_sync"):
        return

    if frappe.db.exists("HD Customer", {"erpnext_customer": doc.name}):
        return

    hd_doc = frappe.get_doc(
        {
            "doctype": "HD Customer",
            "customer_name": doc.customer_name,
            "erpnext_customer": doc.name,
            "image": doc.image,
        }
    )
    hd_doc.flags.ignore_erpnext_sync = True
    hd_doc.insert(ignore_permissions=True)
    set_links(doc.name, hd_doc.name)


def on_update(doc: Document, method: str | None = None):
    if not should_sync() or doc.flags.get("ignore_erpnext_sync"):
        return

    if doc.has_value_changed("image"):
        frappe.db.set_value(
            "HD Customer",
            {"erpnext_customer": doc.name},
            "image",
            doc.image,
        )


def before_rename(
    doc: Document, method: str | None, olddn: str, newdn: str, merge: bool = False
):
    validate_rename_conflict("Customer", olddn, newdn, merge)


def after_rename(
    doc: Document, method: str | None, olddn: str, newdn: str, merge: bool = False
):
    cascade_rename("Customer", olddn, newdn, merge)


def on_trash(doc: Document, method: str | None = None):
    if in_cascade() or not should_sync():
        return

    hd_customer = frappe.db.get_value(
        "HD Customer", {"erpnext_customer": doc.name}, "name"
    )
    if hd_customer:
        # Clear the back-link first so HD Customer's on_trash won't try to
        # delete this Customer again (it's already being deleted).
        frappe.db.set_value("HD Customer", hd_customer, "erpnext_customer", None)
        frappe.delete_doc("HD Customer", hd_customer, ignore_permissions=True)
