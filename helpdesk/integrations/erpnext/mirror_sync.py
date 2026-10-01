import frappe
from frappe.model import default_fields
from frappe.model.document import Document

from helpdesk.integrations.erpnext.utils import (
    ALLOWED_DOCTYPES,
    find_target_for,
    should_sync,
)

# Bidirectional HD↔ERP mirror sync, driven by doc_events.
#
# Each doctype module passes a `config` dict describing how its records map to
# the linked record on the other side:
#
#     "user_field"     str            - field holding the user (e.g. "user")
#     "doctype_field"  str            - field holding the linked doctype name
#                                        (e.g. "allow", "share_doctype")
#     "value_field"    str            - field holding the linked record name
#                                        (e.g. "for_value", "share_name")
#     "extra_dedup_keys" callable(doc) - optional; extra keys for the existing-mirror
#                                        check, to match the parent's own dup check
#     "extra_flags"    callable(mirror) - optional; extra flags to set on a mirror
#                                        before insert/save/delete


def before_validate(doc: Document, config: dict):
    """Clean up the old mirror BEFORE the parent's validate() runs its
    duplicate check. Otherwise an identity change that collides with the
    mirror's identity would trip DuplicateEntryError. If the save later fails,
    the transaction rolls back and the mirror comes back."""
    old = doc.get_doc_before_save()
    if old and has_data_updated(doc, old, config) and sync_active(doc):
        delete_mirror_for(doc, old, config)


def after_insert(doc: Document, config: dict):
    if should_mirror(doc, config):
        create_mirror(doc, config)


def on_update(doc: Document, config: dict):
    if not should_mirror(doc, config):
        return
    old = doc.get_doc_before_save()
    if old and has_data_updated(doc, old, config):
        # Old mirror was cleaned up in before_validate(); create the fresh one.
        create_mirror(doc, config)
    else:
        sync_state_to_mirror(doc, config)


def on_trash(doc: Document, config: dict):
    if not should_mirror(doc, config):
        return
    mirror = find_mirror(doc, config)
    if not mirror:
        return
    set_mirror_flags(mirror, config)
    mirror.delete(ignore_permissions=True)


def should_mirror(doc: Document, config: dict) -> bool:
    if doc.get(config["doctype_field"]) not in ALLOWED_DOCTYPES:
        return False
    return sync_active(doc)


def sync_active(doc: Document) -> bool:
    """True when sync is enabled and this change isn't itself sync-triggered."""
    return should_sync() and not doc.flags.get("ignore_erpnext_sync")


def has_data_updated(doc: Document, old: Document, config: dict) -> bool:
    return any(old.get(f) != doc.get(f) for f in identity_fields(config))


def create_mirror(doc: Document, config: dict):
    """Create the mirror document for this record on the other side."""
    target = find_target_for(
        doc.get(config["doctype_field"]), doc.get(config["value_field"])
    )
    if not target:
        return
    target_doctype, target_value = target
    if frappe.get_all(
        doc.doctype,
        filters=dedup_filter(doc, config, target_doctype, target_value),
        limit=1,
    ):
        return
    mirror = frappe.copy_doc(doc)
    mirror.set(config["doctype_field"], target_doctype)
    mirror.set(config["value_field"], target_value)
    set_mirror_flags(mirror, config)
    mirror.insert(ignore_permissions=True)


def delete_mirror_for(doc: Document, old: Document, config: dict):
    """Find and delete the mirror that corresponded to `old`'s identity."""
    if old.get(config["doctype_field"]) not in ALLOWED_DOCTYPES:
        return
    target = find_target_for(
        old.get(config["doctype_field"]), old.get(config["value_field"])
    )
    if not target:
        return
    target_doctype, target_value = target
    mirror_name = frappe.db.get_value(
        doc.doctype,
        {
            config["user_field"]: old.get(config["user_field"]),
            config["doctype_field"]: target_doctype,
            config["value_field"]: target_value,
        },
    )
    if not mirror_name:
        return
    mirror = frappe.get_doc(doc.doctype, mirror_name)
    set_mirror_flags(mirror, config)
    mirror.delete(ignore_permissions=True)


def sync_state_to_mirror(doc: Document, config: dict):
    """Copy state (non-identity, non-framework) fields to the existing mirror."""
    mirror = find_mirror(doc, config)
    if not mirror:
        return
    changed = False
    for field, value in mirror_data(doc, config).items():
        if mirror.get(field) != value:
            mirror.set(field, value)
            changed = True
    if changed:
        set_mirror_flags(mirror, config)
        mirror.save(ignore_permissions=True)


def find_mirror(doc: Document, config: dict):
    target = find_target_for(
        doc.get(config["doctype_field"]), doc.get(config["value_field"])
    )
    if not target:
        return None
    target_doctype, target_value = target
    mirror_name = frappe.db.get_value(
        doc.doctype,
        {
            config["user_field"]: doc.get(config["user_field"]),
            config["doctype_field"]: target_doctype,
            config["value_field"]: target_value,
        },
    )
    return frappe.get_doc(doc.doctype, mirror_name) if mirror_name else None


def mirror_data(doc: Document, config: dict) -> dict:
    """All meta-defined fields except framework defaults and identity fields.
    Used for syncing field changes to an existing mirror."""
    data = doc.get_valid_dict()
    for field in (*default_fields, *identity_fields(config)):
        data.pop(field, None)
    return data


def dedup_filter(
    doc: Document, config: dict, target_doctype: str, target_value: str
) -> dict:
    """Filter for checking if a mirror already exists. `extra_dedup_keys` lets a
    doctype add keys to match the parent's own dup check."""
    base = {
        config["user_field"]: doc.get(config["user_field"]),
        config["doctype_field"]: target_doctype,
        config["value_field"]: target_value,
    }
    extra_dedup_keys = config.get("extra_dedup_keys")
    if extra_dedup_keys:
        base.update(extra_dedup_keys(doc))
    return base


def set_mirror_flags(mirror: Document, config: dict):
    """Set flags on a mirror doc before insert / save / delete. `extra_flags`
    lets a doctype set additional flags."""
    mirror.flags.ignore_erpnext_sync = True
    extra_flags = config.get("extra_flags")
    if extra_flags:
        extra_flags(mirror)


def identity_fields(config: dict) -> tuple[str, ...]:
    return (config["user_field"], config["doctype_field"], config["value_field"])
