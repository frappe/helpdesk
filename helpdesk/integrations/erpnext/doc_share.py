import frappe
from frappe.core.doctype.docshare.docshare import DocShare
from frappe.model import default_fields

from helpdesk.integrations.erpnext.utils import ALLOWED_DOCTYPES, should_sync

# Identity fields define WHICH share this is — they're what differentiates the
# original from the mirror. Everything else (permissions, flags, etc.) is mirrored.
IDENTITY_FIELDS = ("user", "share_doctype", "share_name")


class CustomDocShare(DocShare):
    """Overrides core DocShare to keep HD Customer / ERPNext Customer shares
    mirrored bidirectionally when the integration is enabled."""

    def after_insert(self):
        super().after_insert()
        if not self._should_mirror():
            return
        self._create_mirror()

    def on_update(self):
        # Core DocShare doesn't define on_update — no super() call needed.
        old = self.get_doc_before_save()
        identity_changed = bool(old) and any(
            old.get(f) != self.get(f) for f in IDENTITY_FIELDS
        )

        # Always try to clean up the old mirror when identity changed, even if
        # the new identity isn't itself mirrorable (e.g., changed to unrelated).
        if (
            identity_changed
            and should_sync()
            and not self.flags.get("ignore_erpnext_sync")
        ):
            self._delete_mirror_for(old)

        if not self._should_mirror():
            return

        if identity_changed:
            self._create_mirror()
        else:
            self._sync_state_to_mirror()

    def on_trash(self):
        super().on_trash()
        if not self._should_mirror():
            return
        mirror = self._find_mirror()
        if not mirror:
            return
        mirror.flags.ignore_erpnext_sync = True
        mirror.flags.ignore_share_permission = True
        mirror.delete(ignore_permissions=True)

    def _create_mirror(self):
        """Create the mirror DocShare for this record on the other side."""
        target = self._find_target_for(self.share_doctype, self.share_name)
        if not target:
            return
        target_doctype, target_name = target
        if frappe.db.exists(
            "DocShare",
            {
                "user": self.user,
                "share_doctype": target_doctype,
                "share_name": target_name,
            },
        ):
            return
        mirror = frappe.copy_doc(self)
        mirror.share_doctype = target_doctype
        mirror.share_name = target_name
        mirror.flags.ignore_erpnext_sync = True
        mirror.flags.ignore_share_permission = True
        mirror.insert(ignore_permissions=True)

    def _delete_mirror_for(self, old):
        """Find and delete the mirror that corresponded to `old`'s identity."""
        if old.get("share_doctype") not in ALLOWED_DOCTYPES:
            return
        target = self._find_target_for(old.get("share_doctype"), old.get("share_name"))
        if not target:
            return
        target_doctype, target_name = target
        mirror_name = frappe.db.get_value(
            "DocShare",
            {
                "user": old.get("user"),
                "share_doctype": target_doctype,
                "share_name": target_name,
            },
        )
        if not mirror_name:
            return
        mirror = frappe.get_doc("DocShare", mirror_name)
        mirror.flags.ignore_erpnext_sync = True
        mirror.flags.ignore_share_permission = True
        mirror.delete(ignore_permissions=True)

    def _sync_state_to_mirror(self):
        """Copy state (non-identity, non-framework) fields to the existing mirror."""
        mirror = self._find_mirror()
        if not mirror:
            return
        changed = False
        for field, value in self._mirror_data().items():
            if mirror.get(field) != value:
                mirror.set(field, value)
                changed = True
        if changed:
            mirror.flags.ignore_erpnext_sync = True
            mirror.flags.ignore_share_permission = True
            mirror.save(ignore_permissions=True)

    def _mirror_data(self) -> dict:
        """All meta-defined fields except framework defaults and identity fields.
        Used for syncing field changes to an existing mirror."""
        data = self.get_valid_dict()
        for field in (*default_fields, *IDENTITY_FIELDS):
            data.pop(field, None)
        return data

    def _should_mirror(self) -> bool:
        if self.share_doctype not in ALLOWED_DOCTYPES:
            return False
        if not should_sync():
            return False
        if self.flags.get("ignore_erpnext_sync"):
            return False
        return True

    @staticmethod
    def _find_target_for(
        share_doctype: str | None, share_name: str | None
    ) -> tuple[str, str] | None:
        """Compute (target_doctype, target_name) for the given identity values."""
        if not share_doctype or not share_name:
            return None
        if share_doctype == "HD Customer":
            erp = frappe.db.get_value("HD Customer", share_name, "erpnext_customer")
            return ("Customer", erp) if erp else None
        if share_doctype == "Customer":
            hd = frappe.db.get_value("Customer", share_name, "hd_customer")
            return ("HD Customer", hd) if hd else None
        return None

    def _find_mirror(self):
        target = self._find_target_for(self.share_doctype, self.share_name)
        if not target:
            return None
        target_doctype, target_name = target
        mirror_name = frappe.db.get_value(
            "DocShare",
            {
                "user": self.user,
                "share_doctype": target_doctype,
                "share_name": target_name,
            },
        )
        return frappe.get_doc("DocShare", mirror_name) if mirror_name else None


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
