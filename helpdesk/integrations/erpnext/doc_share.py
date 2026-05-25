import frappe
from frappe.core.doctype.docshare.docshare import DocShare

from helpdesk.integrations.erpnext.mirror_sync import MirrorSyncMixin
from helpdesk.integrations.erpnext.utils import should_sync


class CustomDocShare(MirrorSyncMixin, DocShare):
    """Overrides core DocShare to keep HD Customer / ERPNext Customer shares
    mirrored bidirectionally when the integration is enabled."""

    DOCTYPE_FIELD = "share_doctype"
    VALUE_FIELD = "share_name"

    def before_validate(self):
        """Clean up the old mirror when identity changes. Mirrored from
        CustomUserPermission for symmetry — done in before_validate so it sits
        before any duplicate-style validation the parent might add."""
        old = self.get_doc_before_save()
        if old and self.has_data_updated(old) and self.sync_active():
            self.delete_mirror_for(old)

    def after_insert(self):
        super().after_insert()
        if self.should_mirror():
            self.create_mirror()

    def on_update(self):
        # Core DocShare doesn't define on_update — no super() call needed.
        if not self.should_mirror():
            return
        old = self.get_doc_before_save()
        if old and self.has_data_updated(old):
            # Old mirror was cleaned up in before_validate(); create the fresh one.
            self.create_mirror()
        else:
            self.sync_state_to_mirror()

    def on_trash(self):
        super().on_trash()
        if not self.should_mirror():
            return
        mirror = self.find_mirror()
        if not mirror:
            return
        self.set_mirror_flags(mirror)
        mirror.delete(ignore_permissions=True)

    def set_mirror_flags(self, mirror):
        super().set_mirror_flags(mirror)
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
