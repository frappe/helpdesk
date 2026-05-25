import frappe
from frappe.core.doctype.user_permission.user_permission import UserPermission
from frappe.utils import cstr

from helpdesk.integrations.erpnext.mirror_sync import MirrorSyncMixin
from helpdesk.integrations.erpnext.utils import should_sync


class CustomUserPermission(MirrorSyncMixin, UserPermission):
    """Overrides core UserPermission to keep HD Customer / ERPNext Customer
    permissions mirrored bidirectionally when the integration is enabled."""

    DOCTYPE_FIELD = "allow"
    VALUE_FIELD = "for_value"

    def before_validate(self):
        """Clean up the old mirror BEFORE Frappe's duplicate-perm check runs
        in validate(). Otherwise an identity change that collides with the
        mirror's identity would trip DuplicateEntryError. If the save later
        fails, the transaction rolls back and the mirror comes back."""
        old = self.get_doc_before_save()
        if old and self.has_data_updated(old) and self.sync_active():
            self.delete_mirror_for(old)

    def after_insert(self):
        # Core UserPermission doesn't define after_insert — no super() call.
        if self.should_mirror():
            self.create_mirror()

    def on_update(self):
        super().on_update()
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

    def dedup_filter(self, target_doctype: str, target_value: str) -> dict:
        # Frappe's validate_user_permission() dedups on these 5 keys; mirror
        # that here so we don't insert a row the parent's validate() would
        # reject as a duplicate.
        return {
            **super().dedup_filter(target_doctype, target_value),
            "applicable_for": cstr(self.applicable_for),
            "apply_to_all_doctypes": self.apply_to_all_doctypes,
        }


def sync_user_permissions():
    """Bulk-sync User Permissions between HD Customer and Customer. Idempotent."""
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

    existing_hd_perms = {(p.user, p.for_value) for p in hd_customer_user_perms}
    existing_erp_perms = {(p.user, p.for_value) for p in erpnext_customer_user_perms}

    # ERP → HD
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

    # HD → ERP
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
