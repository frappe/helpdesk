# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import comma_and

from helpdesk.consts import (
    DEFAULT_TICKET_TEMPLATE,
    NEVER_CUSTOMER_VISIBLE_FIELDS,
    SERVER_COMPUTED_FIELDS,
    TICKET_INTERNAL_FIELD_PERMLEVEL,
)
from helpdesk.field_visibility import fields_visible_to
from helpdesk.utils import capture_event


class HDTicketTemplate(Document):
    def validate(self):
        self.verify_field_exists()
        self.validate_unallowed_fields()
        self.validate_customer_visible_fields()
        self.warn_customer_hidden_fields()

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

    def validate_customer_visible_fields(self):
        """Templates only narrow what permission levels allow, never widen."""
        for f in self.fields:
            if not f.fieldname or f.visible_to == "Agents":
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

    def warn_customer_hidden_fields(self):
        """Hiding covers helpdesk pages only; say so when the API still serves it."""
        if frappe.flags.in_migrate or frappe.flags.in_patch:
            return
        meta = frappe.get_meta("HD Ticket")
        exposed = [
            meta.get_translated_label(f.fieldname)
            for f in self.fields
            if f.fieldname
            and f.visible_to == "Agents"
            and self.current_permlevel(f.fieldname) < TICKET_INTERNAL_FIELD_PERMLEVEL
        ]
        if not exposed:
            return
        link = '<a href="/desk/customize-form?doc_type=HD%20Ticket">{0}</a>'.format(
            _("Customize Form")
        )
        if len(exposed) == 1:
            text = _(
                "{0} is hidden from customers here, but the API still returns it."
                " Raise its permission level in {1} to hide it everywhere."
            ).format(exposed[0], link)
        else:
            text = _(
                "{0} are hidden from customers here, but the API still returns them."
                " Raise their permission levels in {1} to hide them everywhere."
            ).format(comma_and(exposed, add_quotes=False), link)
        frappe.msgprint(text, title=_("Information"), indicator="blue")

    def current_permlevel(self, fieldname: str) -> int:
        """Live meta, so a level changed in Customize Form counts."""
        field = frappe.get_meta("HD Ticket").get_field(fieldname)
        return field.permlevel if field else 0

    def custom_field_exists(self, fieldname: str):
        return frappe.db.exists(
            {
                "doctype": "Custom Field",
                "fieldname": fieldname,
                "dt": "HD Ticket",
            }
        )

    def on_update(self):
        fields_visible_to.clear_cache()
        capture_event("ticket_template_updated")

    def on_trash(self):
        self.prevent_default_delete()

    def prevent_default_delete(self):
        if self.name == DEFAULT_TICKET_TEMPLATE:
            text = _("Default template can not be deleted")
            frappe.throw(text, frappe.PermissionError)
