import frappe

from helpdesk.integrations.erpnext.utils import should_sync


def mirror_doc_share_on_insert(doc, method=None):
    """
    Hook: DocShare — after_insert.

    When a DocShare is created for HD Customer or Customer and the
    integration is enabled, mirror it to the linked counterpart (if not already
    present).  Any other `share_doctype` is ignored.
    """
    allowed_doctypes = ["HD Customer", "Customer"]
    if doc.share_doctype not in allowed_doctypes:
        return

    if not should_sync():
        return

    if doc.flags.get("ignore_erpnext_sync"):
        return

    if doc.share_doctype == "HD Customer":
        # Mirror HD Customer share → Customer
        erpnext_customer = frappe.db.get_value(
            "HD Customer", doc.share_name, "erpnext_customer"
        )
        if not erpnext_customer:
            return
        already_exists = frappe.db.exists(
            "DocShare",
            {
                "user": doc.user,
                "share_doctype": "Customer",
                "share_name": erpnext_customer,
            },
        )
        if already_exists:
            return
        mirrored = frappe.get_doc(
            {
                **doc.as_dict(),
                "doctype": "DocShare",
                "share_doctype": "Customer",
                "share_name": erpnext_customer,
            }
        )
        mirrored.flags.ignore_erpnext_sync = True
        mirrored.flags.ignore_share_permission = True
        mirrored.insert(ignore_permissions=True)
    elif doc.share_doctype == "Customer":
        # Mirror Customer share → HD Customer
        hd_customer = frappe.db.get_value("Customer", doc.share_name, "hd_customer")
        if not hd_customer:
            return
        already_exists = frappe.db.exists(
            "DocShare",
            {
                "user": doc.user,
                "share_doctype": "HD Customer",
                "share_name": hd_customer,
            },
        )
        if already_exists:
            return
        mirrored = frappe.get_doc(
            {
                **doc.as_dict(),
                "doctype": "DocShare",
                "share_doctype": "HD Customer",
                "share_name": hd_customer,
            }
        )
        mirrored.flags.ignore_erpnext_sync = True
        mirrored.flags.ignore_share_permission = True
        mirrored.insert(ignore_permissions=True)


def mirror_doc_share_on_trash(doc, method=None):
    """Hook: DocShare — on_trash."""
    allowed_doctypes = ["HD Customer", "Customer"]
    if doc.share_doctype not in allowed_doctypes:
        return

    if not should_sync():
        return

    if doc.flags.get("ignore_erpnext_sync"):
        return

    if doc.share_doctype == "HD Customer":
        linked_value = frappe.db.get_value(
            "HD Customer", doc.share_name, "erpnext_customer"
        )
        target_doctype = "Customer"
    else:
        linked_value = frappe.db.get_value("Customer", doc.share_name, "hd_customer")
        target_doctype = "HD Customer"

    if not linked_value:
        return

    mirrored_name = frappe.db.get_value(
        "DocShare",
        {
            "user": doc.user,
            "share_doctype": target_doctype,
            "share_name": linked_value,
        },
    )
    if not mirrored_name:
        return

    mirrored = frappe.get_doc("DocShare", mirrored_name)
    mirrored.flags.ignore_erpnext_sync = True
    mirrored.flags.ignore_share_permission = True
    mirrored.delete(ignore_permissions=True)


def sync_shared_docs():
    if not should_sync():
        return

    hd_customer_shares = frappe.get_list(
        "DocShare",
        filters={"share_doctype": "HD Customer"},
        fields=["*"],
    )
    erpnext_customer_shares = frappe.get_list(
        "DocShare",
        filters={"share_doctype": "Customer"},
        fields=["*"],
    )

    # Build lookup sets for deduplication: (user, share_name)
    existing_hd_shares = {(s.user, s.share_name) for s in hd_customer_shares}
    existing_erp_shares = {(s.user, s.share_name) for s in erpnext_customer_shares}

    # ERP → HD: for each Customer share, mirror it to HD Customer if linked
    for share in erpnext_customer_shares:
        hd_customer = frappe.db.get_value("Customer", share.share_name, "hd_customer")
        if not hd_customer:
            continue
        if (share.user, hd_customer) in existing_hd_shares:
            continue
        doc = frappe.get_doc(
            {
                **share,
                "doctype": "DocShare",
                "share_doctype": "HD Customer",
                "share_name": hd_customer,
            }
        )
        doc.flags.ignore_share_permission = True
        doc.flags.ignore_erpnext_sync = True
        doc.insert(ignore_permissions=True)
        existing_hd_shares.add((share.user, hd_customer))

    # HD → ERP: for each HD Customer share, mirror it to Customer if linked
    for share in hd_customer_shares:
        erpnext_customer = frappe.db.get_value(
            "HD Customer", share.share_name, "erpnext_customer"
        )
        if not erpnext_customer:
            continue
        if (share.user, erpnext_customer) in existing_erp_shares:
            continue
        doc = frappe.get_doc(
            {
                **share,
                "doctype": "DocShare",
                "share_doctype": "Customer",
                "share_name": erpnext_customer,
            }
        )
        doc.flags.ignore_share_permission = True
        doc.flags.ignore_erpnext_sync = True
        doc.insert(ignore_permissions=True)
        existing_erp_shares.add((share.user, erpnext_customer))
