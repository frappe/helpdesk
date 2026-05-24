import frappe
from frappe.core.doctype.user_permission.user_permission import UserPermission
from frappe.model import default_fields
from frappe.utils import cstr

from helpdesk.integrations.erpnext.utils import ALLOWED_DOCTYPES, should_sync

# Identity fields define WHICH perm this is — they're what differentiates the
# original from the mirror. Everything else is mirrored.
IDENTITY_FIELDS = ("user", "allow", "for_value")


class CustomUserPermission(UserPermission):
    """Overrides core UserPermission to keep HD Customer / ERPNext Customer
    permissions mirrored bidirectionally when the integration is enabled."""

    def validate(self):
        # If the user is changing identity fields on this perm, the old mirror
        # would conflict with Frappe's duplicate-perm validation when the new
        # identity matches the mirror's. Clean it up BEFORE super().validate()
        # so the framework sees no duplicates. If the save later fails, the
        # transaction rolls back and the mirror comes back.
        old = self.get_doc_before_save()
        if (
            old
            and any(old.get(f) != self.get(f) for f in IDENTITY_FIELDS)
            and should_sync()
            and not self.flags.get("ignore_erpnext_sync")
        ):
            self._delete_mirror_for(old)
        super().validate()

    def after_insert(self):
        # Core UserPermission doesn't define after_insert — no super() call.
        if not self._should_mirror():
            return
        self._create_mirror()

    def on_update(self):
        super().on_update()

        old = self.get_doc_before_save()
        identity_changed = bool(old) and any(
            old.get(f) != self.get(f) for f in IDENTITY_FIELDS
        )

        if not self._should_mirror():
            return

        if identity_changed:
            # Old mirror was cleaned up in validate(); create the fresh mirror now.
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
        mirror.delete(ignore_permissions=True)

    def _create_mirror(self):
        """Create the mirror User Permission for this record on the other side."""
        target = self._find_target_for(self.allow, self.for_value)
        if not target:
            return
        target_allow, target_value = target
        # Double-check not to create a duplicate mirror if one already exists for some reason.
        if frappe.get_all(
            "User Permission",
            filters={
                "user": self.user,
                "allow": target_allow,
                "for_value": target_value,
                "applicable_for": cstr(self.applicable_for),
                "apply_to_all_doctypes": self.apply_to_all_doctypes,
            },
            limit=1,
        ):
            return
        mirror = frappe.copy_doc(self)
        mirror.allow = target_allow
        mirror.for_value = target_value
        mirror.flags.ignore_erpnext_sync = True
        mirror.insert(ignore_permissions=True)

    def _delete_mirror_for(self, old):
        """Find and delete the mirror that corresponded to `old`'s identity."""
        if old.get("allow") not in ALLOWED_DOCTYPES:
            return
        target = self._find_target_for(old.get("allow"), old.get("for_value"))
        if not target:
            return
        target_allow, target_value = target
        mirror_name = frappe.db.get_value(
            "User Permission",
            {
                "user": old.get("user"),
                "allow": target_allow,
                "for_value": target_value,
            },
        )
        if not mirror_name:
            return
        mirror = frappe.get_doc("User Permission", mirror_name)
        mirror.flags.ignore_erpnext_sync = True
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
            mirror.save(ignore_permissions=True)

    def _mirror_data(self) -> dict:
        """All meta-defined fields except framework defaults and identity fields.
        Used for syncing field changes to an existing mirror."""
        data = self.get_valid_dict()
        for field in (*default_fields, *IDENTITY_FIELDS):
            data.pop(field, None)
        return data

    def _should_mirror(self) -> bool:
        if self.allow not in ALLOWED_DOCTYPES:
            return False
        if not should_sync():
            return False
        if self.flags.get("ignore_erpnext_sync"):
            return False
        return True

    @staticmethod
    def _find_target_for(
        allow: str | None, for_value: str | None
    ) -> tuple[str, str] | None:
        """Compute (target_allow, target_value) for the given identity values."""
        if not allow or not for_value:
            return None
        if allow == "HD Customer":
            erp = frappe.db.get_value("Customer", {"hd_customer": for_value}, "name")
            return ("Customer", erp) if erp else None
        if allow == "Customer":
            hd = frappe.db.get_value(
                "HD Customer", {"erpnext_customer": for_value}, "name"
            )
            return ("HD Customer", hd) if hd else None
        return None

    def _find_mirror(self):
        target = self._find_target_for(self.allow, self.for_value)
        if not target:
            return None
        target_allow, target_value = target
        mirror_name = frappe.db.get_value(
            "User Permission",
            {"user": self.user, "allow": target_allow, "for_value": target_value},
        )
        return frappe.get_doc("User Permission", mirror_name) if mirror_name else None


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
