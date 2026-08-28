# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from helpdesk.consts import (
    DEFAULT_TICKET_TEMPLATE,
    SERVER_COMPUTED_FIELDS,
    TICKET_INTERNAL_FIELD_PERMLEVEL,
    TICKET_VISIBLE_FIELD_PERMLEVEL,
)
from helpdesk.utils import capture_event


def has_recorded_base(level) -> bool:
    """-1 is the column default: no base level recorded yet."""
    return level is not None and level >= 0


class HDTicketTemplate(Document):
    def validate(self):
        self.verify_field_exists()
        self.validate_unallowed_fields()
        self.validate_unfillable_fields_stay_hidden()

    def verify_field_exists(self):
        for f in self.fields:
            if not f.fieldname:
                continue
            exists = self.docfield_exists(f.fieldname) or self.custom_field_exists(
                f.fieldname
            )
            if not exists:
                text = _("Field `{0}` does not exist in Ticket").format(f.fieldname)
                frappe.throw(text)

    def docfield_exists(self, fieldname: str):
        return frappe.db.exists(
            {
                "doctype": "DocField",
                "fieldname": fieldname,
                "parent": "HD Ticket",
            }
        )

    def validate_unallowed_fields(self):
        unallowed_fields = ["status", "agreement_status"]
        for f in self.fields:
            if f.fieldname in unallowed_fields:
                text = _("Field `{0}` is not allowed in Ticket Template").format(
                    f.fieldname
                )
                frappe.throw(text)

    def validate_unfillable_fields_stay_hidden(self):
        """An internal field must stay hidden, so only agents can fill it.
        Showing it offers the customer an input the server throws away."""
        for f in self.fields:
            if not f.fieldname or f.hide_from_customer:
                continue
            if f.fieldname in SERVER_COMPUTED_FIELDS:
                text = _(
                    "Field `{0}` is set by the system and cannot be shown to customers"
                ).format(f.fieldname)
                frappe.throw(text)
            if self.owns_custom_field_permlevels() and self.custom_field_exists(
                f.fieldname
            ):
                # the sync lowers a shown custom field itself
                continue
            if self.current_permlevel(f.fieldname) >= TICKET_INTERNAL_FIELD_PERMLEVEL:
                text = _(
                    "Field `{0}` is internal and cannot be shown to customers."
                    " Lower its permission level in Customize Form to show it."
                ).format(f.fieldname)
                frappe.throw(text)

    def custom_field_exists(self, fieldname: str):
        return frappe.db.exists(
            {
                "doctype": "Custom Field",
                "fieldname": fieldname,
                "dt": "HD Ticket",
            }
        )

    def on_update(self):
        if self.owns_custom_field_permlevels():
            moved = self.sync_custom_field_permlevels()
            moved = self.restore_removed_custom_fields() or moved
            if moved:
                frappe.clear_cache(doctype="HD Ticket")
        capture_event("ticket_template_updated")

    def owns_custom_field_permlevels(self) -> bool:
        """HD Ticket has one set of field levels, so only one template can
        drive them: the Default one."""
        return self.name == DEFAULT_TICKET_TEMPLATE

    def sync_custom_field_permlevels(self) -> bool:
        """Shown custom fields sit at the customer-visible level, hidden ones
        at the internal level. Each row remembers the level its field arrived
        with, so a removed row can hand it back."""
        moved = False
        for f in self.fields:
            if not self.custom_field_exists(f.fieldname):
                continue
            current = self.current_permlevel(f.fieldname)
            self.remember_base_permlevel(f, current)
            target = (
                TICKET_INTERNAL_FIELD_PERMLEVEL
                if f.hide_from_customer
                else TICKET_VISIBLE_FIELD_PERMLEVEL
            )
            if current != target:
                self.set_custom_field_permlevel(f.fieldname, target)
                moved = True
        return moved

    def remember_base_permlevel(self, row, current: int):
        """A save can replace rows wholesale, so a fresh row inherits the
        base its predecessor recorded rather than the level the sync last
        set."""
        if has_recorded_base(row.base_permlevel):
            return
        base = self.bases_before_save().get(row.fieldname)
        if not has_recorded_base(base):
            base = current
        row.db_set("base_permlevel", base, update_modified=False)

    def restore_removed_custom_fields(self) -> bool:
        """A removed row hands the field back at the level it arrived with,
        so a template round trip leaves no trace."""
        kept = {f.fieldname for f in self.fields}
        moved = False
        for fieldname, base in self.bases_before_save().items():
            if fieldname in kept or not has_recorded_base(base):
                continue
            if not self.custom_field_exists(fieldname):
                continue
            if self.current_permlevel(fieldname) != base:
                self.set_custom_field_permlevel(fieldname, base)
                moved = True
        return moved

    def bases_before_save(self) -> dict:
        before = self.get_doc_before_save()
        if not before:
            return {}
        return {f.fieldname: f.base_permlevel for f in before.fields}

    def set_custom_field_permlevel(self, fieldname: str, level: int):
        frappe.db.set_value(
            "Custom Field",
            {"dt": "HD Ticket", "fieldname": fieldname},
            "permlevel",
            level,
        )

    def current_permlevel(self, fieldname: str) -> int:
        """Read from live meta, not the shipped DocField row, so a level an
        administrator changed in Customize Form is recognised."""
        field = frappe.get_meta("HD Ticket").get_field(fieldname)
        return field.permlevel if field else 0

    def on_trash(self):
        self.prevent_default_delete()

    def prevent_default_delete(self):
        if self.name == DEFAULT_TICKET_TEMPLATE:
            text = _("Default template can not be deleted")
            frappe.throw(text, frappe.PermissionError)
