import frappe
from frappe import _
from frappe.model.rename_doc import rename_doc

CASCADE_FLAG = "erpnext_hd_cascade_in_progress"

# Doctypes whose hooks the integration touches. Anything else is a no-op.
ALLOWED_DOCTYPES = ("HD Customer", "Customer")


def should_sync():
    return "erpnext" in frappe.get_installed_apps() and frappe.db.get_single_value(
        "ERPNext HD Settings", "enabled"
    )


def set_links(erpnext_customer_name: str, hd_customer_name: str):
    frappe.db.set_value(
        "HD Customer",
        hd_customer_name,
        "erpnext_customer",
        erpnext_customer_name,
        update_modified=False,
    )
    frappe.db.set_value(
        "Customer",
        erpnext_customer_name,
        "hd_customer",
        hd_customer_name,
        update_modified=False,
    )


def create_customer_field():
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

    if "erpnext" not in frappe.get_installed_apps():
        return

    create_custom_fields(
        {
            "Customer": [
                {
                    "fieldname": "hd_customer",
                    "fieldtype": "Data",
                    "label": "HD Customer",
                    "read_only": 1,
                    "insert_after": "customer_name",
                    "hidden": 1,
                }
            ]
        }
    )


def in_cascade() -> bool:
    return bool(frappe.flags.get(CASCADE_FLAG))


def _other_side(self_doctype: str) -> tuple[str, str]:
    if self_doctype == "HD Customer":
        return "Customer", "hd_customer"
    return "HD Customer", "erpnext_customer"


def validate_rename_conflict(
    self_doctype: str, olddn: str, newdn: str, merge: bool
) -> None:
    """Called from before_rename. Throws ValidationError if the rename would
    conflict with an unrelated record on the other side."""
    if in_cascade() or not should_sync():
        return

    other_doctype, other_link_field = _other_side(self_doctype)
    linked_name = frappe.db.get_value(other_doctype, {other_link_field: olddn}, "name")
    if not linked_name:
        return

    if merge:
        surviving_name = frappe.db.get_value(
            other_doctype, {other_link_field: newdn}, "name"
        )
        if surviving_name:
            # M2: cascade-merge into surviving_name. No external conflict.
            return
        # M1: transfer — target name on other side must be available.

    if linked_name == newdn:
        return

    if frappe.db.exists(other_doctype, newdn):
        existing_link = frappe.db.get_value(other_doctype, newdn, other_link_field)
        if existing_link != olddn:
            frappe.throw(
                _(
                    "Cannot rename: an unrelated {0} '{1}' already exists on the "
                    "other side. Resolve the conflict manually first."
                ).format(other_doctype, newdn)
            )


def cascade_rename(self_doctype: str, olddn: str, newdn: str, merge: bool) -> None:
    """Called from after_rename. Cascades the rename/merge to the linked
    record on the other side and keeps both Data fields in sync."""
    if in_cascade() or not should_sync():
        return

    other_doctype, other_link_field = _other_side(self_doctype)
    linked_name = frappe.db.get_value(other_doctype, {other_link_field: olddn}, "name")
    if not linked_name:
        return

    frappe.flags[CASCADE_FLAG] = True
    try:
        if merge:
            surviving_name = frappe.db.get_value(
                other_doctype, {other_link_field: newdn}, "name"
            )
            if surviving_name and surviving_name != linked_name:
                # M2 — cascade-merge linked_name into surviving_name
                rename_doc(
                    other_doctype,
                    linked_name,
                    surviving_name,
                    merge=True,
                    ignore_permissions=True,
                )
                target_name = surviving_name
            else:
                # M1 — transfer the link by renaming linked_name to newdn
                if linked_name != newdn:
                    rename_doc(
                        other_doctype,
                        linked_name,
                        newdn,
                        ignore_permissions=True,
                    )
                target_name = newdn
        else:
            # P1 — plain cascade-rename
            if linked_name != newdn:
                rename_doc(
                    other_doctype,
                    linked_name,
                    newdn,
                    ignore_permissions=True,
                )
            target_name = newdn

        _resync_data_fields(self_doctype, newdn, target_name)
    finally:
        frappe.flags[CASCADE_FLAG] = False


def _resync_data_fields(self_doctype: str, self_name: str, other_name: str) -> None:
    """After a cascade, both Data fields must point at each other by the new
    names. set_value with update_modified=False to avoid touching timestamps."""
    if self_doctype == "HD Customer":
        hd_name, erp_name = self_name, other_name
    else:
        hd_name, erp_name = other_name, self_name

    if frappe.db.exists("HD Customer", hd_name):
        frappe.db.set_value(
            "HD Customer",
            hd_name,
            "erpnext_customer",
            erp_name,
            update_modified=False,
        )
    if frappe.db.exists("Customer", erp_name):
        frappe.db.set_value(
            "Customer",
            erp_name,
            "hd_customer",
            hd_name,
            update_modified=False,
        )


def find_target_for(doctype: str | None, value: str | None) -> tuple[str, str] | None:
    """Map (HD Customer, name) ↔ (Customer, name) via the link fields on each
    side. Returns None when no counterpart exists or inputs are missing."""
    if not doctype or not value:
        return None
    if doctype == "HD Customer":
        erp = frappe.db.get_value("Customer", {"hd_customer": value}, "name")
        return ("Customer", erp) if erp else None
    if doctype == "Customer":
        hd = frappe.db.get_value("HD Customer", {"erpnext_customer": value}, "name")
        return ("HD Customer", hd) if hd else None
    return None
