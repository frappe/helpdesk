import frappe
from frappe.model.document import Document

from helpdesk.integrations.erpnext import mirror_sync
from helpdesk.integrations.erpnext.utils import should_sync

# Keeps HD Customer / ERPNext Customer DocShares mirrored bidirectionally when
# the integration is enabled.


def before_validate(doc: Document, method: str | None = None):
    mirror_sync.before_validate(doc, _config())


def after_insert(doc: Document, method: str | None = None):
    mirror_sync.after_insert(doc, _config())


def on_update(doc: Document, method: str | None = None):
    mirror_sync.on_update(doc, _config())


def on_trash(doc: Document, method: str | None = None):
    mirror_sync.on_trash(doc, _config())


def _config() -> dict:
    return {
        "user_field": "user",
        "doctype_field": "share_doctype",
        "value_field": "share_name",
        "extra_flags": _extra_flags,
    }


def _extra_flags(mirror: Document):
    mirror.flags.ignore_share_permission = True


def sync_shared_docs():
    """Bulk-sync DocShares between HD Customer and Customer. Idempotent — safe
    to call repeatedly. Used by the ERPNext settings 'Sync Customers' action."""
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

    existing_hd_shares = {(s.user, s.share_name) for s in hd_customer_shares}
    existing_erp_shares = {(s.user, s.share_name) for s in erpnext_customer_shares}

    # ERP → HD
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

    # HD → ERP
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
