import frappe

from helpdesk.integrations.erpnext.utils import should_sync


def mirror_user_permission_on_insert(doc, method=None):
    """
    Hook: User Permission — after_insert.

    When a User Permission is created for HD Customer or Customer and the
    integration is enabled, mirror it to the linked counterpart (if not already
    present).  Any other `allow` doctype is ignored.
    """
    allowed_doctypes = ["HD Customer", "Customer"]
    if doc.allow not in allowed_doctypes:
        return

    if not should_sync():
        return

    if doc.flags.get("ignore_erpnext_sync"):
        return

    if doc.allow == "HD Customer":
        # Mirror HD Customer perm → Customer
        erpnext_customer = frappe.db.get_value(
            "HD Customer", doc.for_value, "erpnext_customer"
        )
        if not erpnext_customer:
            return
        already_exists = frappe.db.exists(
            "User Permission",
            {
                "user": doc.user,
                "allow": "Customer",
                "for_value": erpnext_customer,
            },
        )
        if already_exists:
            return
        mirrored = frappe.get_doc(
            {
                "doctype": "User Permission",
                "user": doc.user,
                "allow": "Customer",
                "for_value": erpnext_customer,
                "apply_to_all_doctypes": doc.apply_to_all_doctypes,
                "applicable_for": doc.applicable_for,
                "hide_descendants": doc.hide_descendants,
                "is_default": doc.is_default,
            }
        )
        mirrored.flags.ignore_erpnext_sync = True
        mirrored.insert(ignore_permissions=True)
    elif doc.allow == "Customer":
        # Mirror Customer perm → HD Customer
        hd_customer = frappe.db.get_value("Customer", doc.for_value, "hd_customer")
        if not hd_customer:
            return
        already_exists = frappe.db.exists(
            "User Permission",
            {
                "user": doc.user,
                "allow": "HD Customer",
                "for_value": hd_customer,
            },
        )
        if already_exists:
            return
        mirrored = frappe.get_doc(
            {
                "doctype": "User Permission",
                "user": doc.user,
                "allow": "HD Customer",
                "for_value": hd_customer,
                "apply_to_all_doctypes": doc.apply_to_all_doctypes,
                "applicable_for": doc.applicable_for,
                "hide_descendants": doc.hide_descendants,
                "is_default": doc.is_default,
            }
        )
        mirrored.flags.ignore_erpnext_sync = True
        mirrored.insert(ignore_permissions=True)


def mirror_user_permission_on_trash(doc, method=None):
    """Hook: User Permission — on_trash."""
    allowed_doctypes = ["HD Customer", "Customer"]
    if doc.allow not in allowed_doctypes:
        return

    if not should_sync():
        return

    if doc.flags.get("ignore_erpnext_sync"):
        return

    if doc.allow == "HD Customer":
        linked_value = frappe.db.get_value(
            "HD Customer", doc.for_value, "erpnext_customer"
        )
        target_allow = "Customer"
    else:
        linked_value = frappe.db.get_value("Customer", doc.for_value, "hd_customer")
        target_allow = "HD Customer"

    if not linked_value:
        return

    mirrored_name = frappe.db.get_value(
        "User Permission",
        {"user": doc.user, "allow": target_allow, "for_value": linked_value},
    )
    if not mirrored_name:
        return

    mirrored = frappe.get_doc("User Permission", mirrored_name)
    mirrored.flags.ignore_erpnext_sync = True
    mirrored.delete(ignore_permissions=True)


def sync_user_permissions():
    if not should_sync():
        return

    hd_customer_user_perms = frappe.get_list(
        "User Permission",
        filters={"allow": "HD Customer"},
        fields=["*"],
    )
    erpnext_customer_user_perms = frappe.get_list(
        "User Permission",
        filters={"allow": "Customer"},
        fields=["*"],
    )

    # Build lookup sets for deduplication: (user, for_value)
    existing_hd_perms = {(p.user, p.for_value) for p in hd_customer_user_perms}
    existing_erp_perms = {(p.user, p.for_value) for p in erpnext_customer_user_perms}

    # ERP → HD: for each Customer perm, mirror it to HD Customer if linked
    for perm in erpnext_customer_user_perms:
        hd_customer = frappe.db.get_value("Customer", perm.for_value, "hd_customer")
        if not hd_customer:
            continue
        if (perm.user, hd_customer) in existing_hd_perms:
            continue
        doc = frappe.get_doc(
            {
                **perm,
                "doctype": "User Permission",
                "allow": "HD Customer",
                "for_value": hd_customer,
            }
        )
        doc.flags.ignore_erpnext_sync = True
        doc.insert(ignore_permissions=True)
        existing_hd_perms.add((perm.user, hd_customer))

    # HD → ERP: for each HD Customer perm, mirror it to Customer if linked
    for perm in hd_customer_user_perms:
        erpnext_customer = frappe.db.get_value(
            "HD Customer", perm.for_value, "erpnext_customer"
        )
        if not erpnext_customer:
            continue
        if (perm.user, erpnext_customer) in existing_erp_perms:
            continue
        doc = frappe.get_doc(
            {
                **perm,
                "doctype": "User Permission",
                "allow": "Customer",
                "for_value": erpnext_customer,
            }
        )
        doc.flags.ignore_erpnext_sync = True
        doc.insert(ignore_permissions=True)
        existing_erp_perms.add((perm.user, erpnext_customer))
