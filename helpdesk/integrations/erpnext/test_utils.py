import frappe


def enable_erpnext_sync():
    frappe.db.set_single_value("ERPNext HD Settings", "enabled", 1)


def disable_erpnext_sync():
    frappe.db.set_single_value("ERPNext HD Settings", "enabled", 0)


def make_erpnext_customer(customer_name: str, **kwargs) -> "frappe.Document":
    """
    Insert an ERPNext Customer with ignore_erpnext_sync=True so that no HD Customer is created as a side-effect.
    """
    doc = frappe.get_doc(
        {"doctype": "Customer", "customer_name": customer_name, **kwargs}
    )
    doc.flags.ignore_erpnext_sync = True
    doc.insert(ignore_permissions=True)
    return doc


def make_hd_customer(customer_name: str, **kwargs) -> "frappe.Document":
    """
    Insert an HD Customer with ignore_erpnext_sync=True so that no ERP Customer
    is created as a side-effect
    """
    doc = frappe.get_doc(
        {"doctype": "HD Customer", "customer_name": customer_name, **kwargs}
    )
    doc.flags.ignore_erpnext_sync = True
    doc.insert(ignore_permissions=True)
    return doc


def make_user_permission(
    user: str, allow: str, for_value: str, apply_to_all_doctypes: int = 1
) -> "frappe.Document":
    """
    Insert a User Permission record for the given user, doctype, and value.
    Returns the inserted document.
    """
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
    """
    Insert a User Permission record without triggering the ERPNext mirror hook.
    Use this in test setup when pre-creating a perm that should not cause a
    real-time mirror to fire (e.g. to test deduplication logic).
    """
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
