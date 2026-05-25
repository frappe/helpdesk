import frappe
from frappe.model import default_fields
from frappe.model.document import Document

from helpdesk.integrations.erpnext.utils import ALLOWED_DOCTYPES, should_sync


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


class MirrorSyncMixin(Document):
    """Shared helpers for bidirectional HD↔ERP mirror sync. Each subclass
    defines its own lifecycle hooks (before_validate, after_insert, on_update,
    on_trash) and calls these helpers as needed.

    Subclasses set:
        DOCTYPE_FIELD - field holding the linked doctype name
                        (e.g. "allow" on User Permission, "share_doctype" on DocShare).
        VALUE_FIELD   - field holding the linked record name
                        (e.g. "for_value", "share_name").
        USER_FIELD    - field holding the user (default "user").

    And override these extension points as needed:
        dedup_filter(target_doctype, target_value) - filter for the existing-mirror
            check; extend with doctype-specific keys to match the parent's own
            duplicate-check (e.g. UserPermission's 5-key check).
        set_mirror_flags(mirror) - set additional flags on a mirror before
            insert/save/delete (e.g. ignore_share_permission for DocShare).
    """

    USER_FIELD: str = "user"
    DOCTYPE_FIELD: str = ""
    VALUE_FIELD: str = ""

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not cls.DOCTYPE_FIELD:
            raise TypeError(
                f"{cls.__name__} must set DOCTYPE_FIELD on the class "
                f"(the field holding the linked doctype name)."
            )
        if not cls.VALUE_FIELD:
            raise TypeError(
                f"{cls.__name__} must set VALUE_FIELD on the class "
                f"(the field holding the linked record name)."
            )

    @property
    def identity_fields(self) -> tuple[str, ...]:
        return (self.USER_FIELD, self.DOCTYPE_FIELD, self.VALUE_FIELD)

    def should_mirror(self) -> bool:
        if self.get(self.DOCTYPE_FIELD) not in ALLOWED_DOCTYPES:
            return False
        return self.sync_active()

    def sync_active(self) -> bool:
        """True when sync is enabled and this change isn't itself sync-triggered."""
        return should_sync() and not self.flags.get("ignore_erpnext_sync")

    def has_data_updated(self, old) -> bool:
        return any(old.get(f) != self.get(f) for f in self.identity_fields)

    def create_mirror(self):
        """Create the mirror document for this record on the other side."""
        target = find_target_for(
            self.get(self.DOCTYPE_FIELD), self.get(self.VALUE_FIELD)
        )
        if not target:
            return
        target_doctype, target_value = target
        if frappe.get_all(
            self.doctype,
            filters=self.dedup_filter(target_doctype, target_value),
            limit=1,
        ):
            return
        mirror = frappe.copy_doc(self)
        mirror.set(self.DOCTYPE_FIELD, target_doctype)
        mirror.set(self.VALUE_FIELD, target_value)
        self.set_mirror_flags(mirror)
        mirror.insert(ignore_permissions=True)

    def delete_mirror_for(self, old):
        """Find and delete the mirror that corresponded to `old`'s identity."""
        if old.get(self.DOCTYPE_FIELD) not in ALLOWED_DOCTYPES:
            return
        target = find_target_for(old.get(self.DOCTYPE_FIELD), old.get(self.VALUE_FIELD))
        if not target:
            return
        target_doctype, target_value = target
        mirror_name = frappe.db.get_value(
            self.doctype,
            {
                self.USER_FIELD: old.get(self.USER_FIELD),
                self.DOCTYPE_FIELD: target_doctype,
                self.VALUE_FIELD: target_value,
            },
        )
        if not mirror_name:
            return
        mirror = frappe.get_doc(self.doctype, mirror_name)
        self.set_mirror_flags(mirror)
        mirror.delete(ignore_permissions=True)

    def sync_state_to_mirror(self):
        """Copy state (non-identity, non-framework) fields to the existing mirror."""
        mirror = self.find_mirror()
        if not mirror:
            return
        changed = False
        for field, value in self.mirror_data().items():
            if mirror.get(field) != value:
                mirror.set(field, value)
                changed = True
        if changed:
            self.set_mirror_flags(mirror)
            mirror.save(ignore_permissions=True)

    def find_mirror(self):
        target = find_target_for(
            self.get(self.DOCTYPE_FIELD), self.get(self.VALUE_FIELD)
        )
        if not target:
            return None
        target_doctype, target_value = target
        mirror_name = frappe.db.get_value(
            self.doctype,
            {
                self.USER_FIELD: self.get(self.USER_FIELD),
                self.DOCTYPE_FIELD: target_doctype,
                self.VALUE_FIELD: target_value,
            },
        )
        return frappe.get_doc(self.doctype, mirror_name) if mirror_name else None

    def mirror_data(self) -> dict:
        """All meta-defined fields except framework defaults and identity fields.
        Used for syncing field changes to an existing mirror."""
        data = self.get_valid_dict()
        for field in (*default_fields, *self.identity_fields):
            data.pop(field, None)
        return data

    def dedup_filter(self, target_doctype: str, target_value: str) -> dict:
        """Filter for checking if a mirror already exists. Subclasses can
        extend with doctype-specific keys to match the parent's dup check."""
        return {
            self.USER_FIELD: self.get(self.USER_FIELD),
            self.DOCTYPE_FIELD: target_doctype,
            self.VALUE_FIELD: target_value,
        }

    def set_mirror_flags(self, mirror):
        """Set flags on a mirror doc before insert / save / delete.
        Subclasses can extend to set additional flags."""
        mirror.flags.ignore_erpnext_sync = True
