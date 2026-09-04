# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from helpdesk.consts import (
    DEFAULT_TICKET_TEMPLATE,
    NEVER_CUSTOMER_VISIBLE_FIELDS,
    SERVER_COMPUTED_FIELDS,
    TICKET_INTERNAL_FIELD_PERMLEVEL,
)
from helpdesk.field_visibility import VISIBILITY_RANKS, get_field_tiers
from helpdesk.utils import capture_event


class HDTicketTemplate(Document):
    def validate(self):
        self.verify_field_exists()
        self.validate_unallowed_fields()
        self.sync_visibility_flags()
        self.validate_unfillable_fields_stay_hidden()
        self.warn_when_meta_narrower_than_permlevel()

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

    def sync_visibility_flags(self):
        # visible_to is what admins edit; hide_from_customer stays synced for
        # the portal Vue, and rows saved before the tier column existed
        # self-heal from the old flag
        for row in self.fields:
            # the save pipeline fills Select defaults into brand-new rows, so
            # a fresh row carrying "Everyone" next to an explicit hide flag is
            # legacy input and the flag wins; saved rows trust visible_to.
            # unrecognised values (a renamed label) re-derive from the flag too
            legacy_row = row.visible_to not in VISIBILITY_RANKS or (
                row.is_new() and row.visible_to == "Everyone" and row.hide_from_customer
            )
            if legacy_row:
                row.visible_to = (
                    "Agents and above" if row.hide_from_customer else "Everyone"
                )
            row.hide_from_customer = int(row.visible_to != "Everyone")

    def validate_unfillable_fields_stay_hidden(self):
        """Templates only narrow what permission levels allow, never widen.
        Showing an internal field offers the customer an input the server
        throws away."""
        for f in self.fields:
            if not f.fieldname or f.visible_to != "Everyone":
                continue
            if f.fieldname in NEVER_CUSTOMER_VISIBLE_FIELDS:
                text = _(
                    "Field `{0}` is a secret and can never be shown to customers"
                ).format(f.fieldname)
                frappe.throw(text)
            if f.fieldname in SERVER_COMPUTED_FIELDS:
                text = _(
                    "Field `{0}` is set by the system and cannot be shown to customers"
                ).format(f.fieldname)
                frappe.throw(text)
            if self.current_permlevel(f.fieldname) >= TICKET_INTERNAL_FIELD_PERMLEVEL:
                text = _(
                    "Field `{0}` is internal and cannot be shown to customers."
                    " Lower its permission level in Customize Form to show it."
                ).format(f.fieldname)
                frappe.throw(text)

    def warn_when_meta_narrower_than_permlevel(self):
        """Hiding here only affects helpdesk pages; the API answers to
        permission levels. Tell the admin when the two disagree."""
        if frappe.flags.in_migrate or frappe.flags.in_patch:
            return
        exposed = [
            f.fieldname
            for f in self.fields
            if f.fieldname
            and f.visible_to != "Everyone"
            and self.current_permlevel(f.fieldname) < TICKET_INTERNAL_FIELD_PERMLEVEL
        ]
        if not exposed:
            return
        frappe.msgprint(
            _(
                "{0} are hidden here but still readable through the API at their"
                " current permission level. Raise the level in Customize Form to"
                " hide them fully."
            ).format(", ".join(exposed)),
            indicator="orange",
        )

    def custom_field_exists(self, fieldname: str):
        return frappe.db.exists(
            {
                "doctype": "Custom Field",
                "fieldname": fieldname,
                "dt": "HD Ticket",
            }
        )

    def on_update(self):
        get_field_tiers.clear_cache()
        capture_event("ticket_template_updated")

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
