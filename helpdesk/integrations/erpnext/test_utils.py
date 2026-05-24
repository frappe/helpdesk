import frappe


def enable_erpnext_sync():
    frappe.db.set_single_value("ERPNext HD Settings", "enabled", 1)


def disable_erpnext_sync():
    frappe.db.set_single_value("ERPNext HD Settings", "enabled", 0)


def make_erpnext_customer(customer_name: str, **kwargs) -> "frappe.Document":
    """Insert an ERPNext Customer with ignore_erpnext_sync=True so that no HD
    Customer is created as a side-effect."""
    doc = frappe.get_doc(
        {"doctype": "Customer", "customer_name": customer_name, **kwargs}
    )
    doc.flags.ignore_erpnext_sync = True
    doc.insert(ignore_permissions=True)
    return doc


def make_hd_customer(customer_name: str, **kwargs) -> "frappe.Document":
    """Insert an HD Customer with ignore_erpnext_sync=True so that no ERP Customer
    is created as a side-effect."""
    doc = frappe.get_doc(
        {"doctype": "HD Customer", "customer_name": customer_name, **kwargs}
    )
    doc.flags.ignore_erpnext_sync = True
    doc.insert(ignore_permissions=True)
    return doc


def make_user_permission(
    user: str, allow: str, for_value: str, apply_to_all_doctypes: int = 1
) -> "frappe.Document":
    """Insert a User Permission record for the given user, doctype, and value."""
    doc = frappe.get_doc(
        {
            "doctype": "User Permission",
            "user": user,
            "allow": allow,
            "for_value": for_value,
            "apply_to_all_doctypes": apply_to_all_doctypes,
        }
    )
    doc.insert(ignore_permissions=True)
    return doc


def make_user_permission_no_sync(
    user: str, allow: str, for_value: str, apply_to_all_doctypes: int = 1
) -> "frappe.Document":
    """Insert a User Permission record without triggering the ERPNext mirror hook.
    Use this in test setup when pre-creating a perm that should not cause a
    real-time mirror to fire (e.g. to test deduplication logic)."""
    doc = frappe.get_doc(
        {
            "doctype": "User Permission",
            "user": user,
            "allow": allow,
            "for_value": for_value,
            "apply_to_all_doctypes": apply_to_all_doctypes,
        }
    )
    doc.flags.ignore_erpnext_sync = True
    doc.insert(ignore_permissions=True)
    return doc


def make_doc_share(
    share_doctype: str,
    share_name: str,
    ignore_erpnext_sync: bool = False,
    **perms,
) -> "frappe.Document":
    """Insert a DocShare for Administrator. Defaults to read=1; pass **perms to override."""
    share = frappe.get_doc(
        {
            "doctype": "DocShare",
            "user": "Administrator",
            "share_doctype": share_doctype,
            "share_name": share_name,
            "read": 1,
            "write": 0,
            "share": 0,
            "submit": 0,
            "everyone": 0,
            **perms,
        }
    )
    share.flags.ignore_share_permission = True
    if ignore_erpnext_sync:
        share.flags.ignore_erpnext_sync = True
    share.insert(ignore_permissions=True)
    return share


def link_customers(
    test_case, base_name: str
) -> tuple["frappe.Document", "frappe.Document"]:
    """Create a linked HD/ERP pair with distinct names ("<base> HD" / "<base> ERP"),
    register cleanups on the test case, return (hd, erp)."""
    erp = make_erpnext_customer(f"{base_name} ERP")
    hd = make_hd_customer(f"{base_name} HD", erpnext_customer=erp.name)
    frappe.db.set_value("Customer", erp.name, "hd_customer", hd.name)
    test_case.addCleanup(frappe.delete_doc, "Customer", erp.name, force=True)
    test_case.addCleanup(frappe.delete_doc, "HD Customer", hd.name, force=True)
    return hd, erp


def make_linked_pair(
    hd_name: str, erp_name: str | None = None
) -> tuple["frappe.Document", "frappe.Document"]:
    """Create a linked HD/ERP pair with custom names (no auto-cleanup). Rename
    tests need this because record names change during the test."""
    erp_name = erp_name or hd_name
    hd = make_hd_customer(hd_name)
    erp = make_erpnext_customer(erp_name, hd_customer=hd.name)
    frappe.db.set_value("HD Customer", hd.name, "erpnext_customer", erp.name)
    return hd, erp


def safe_delete(doctype: str, name: str) -> None:
    """Delete a record if it exists. Use as addCleanup target when the record's
    name may have changed during the test (rename tests)."""
    if name and frappe.db.exists(doctype, name):
        frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)


def cleanup_user_permission(user: str, allow: str, for_value: str) -> None:
    """Delete a User Permission if it exists. Use as addCleanup target when the
    name is unknown ahead of time (e.g. it was created by a sync hook)."""
    name = frappe.db.get_value(
        "User Permission", {"user": user, "allow": allow, "for_value": for_value}
    )
    if name:
        frappe.delete_doc("User Permission", name, force=True)
