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
from helpdesk.field_visibility import get_template_hidden_fields
from helpdesk.utils import capture_event

# the Permission Level section of the framework docs, for the hide warning below
PERMISSION_LEVEL_DOCS = (
    "https://docs.frappe.io/framework/user/en/basics/users-and-permissions"
    "#permission-level"
)


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
        if not self.rows_changed():
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
        # opens in a new tab so an unsaved template is not lost
        docs = '<a href="{0}" target="_blank">{1}</a>'.format(
            PERMISSION_LEVEL_DOCS, _("here")
        )
        if len(exposed) == 1:
            text = _(
                "{0} is hidden from customers here, but the API still returns it."
                " Raise its permission level in {1} to hide it everywhere."
                " Read more about permission levels {2}."
            ).format(exposed[0], link, docs)
        else:
            text = _(
                "{0} are hidden from customers here, but the API still returns them."
                " Raise their permission levels in {1} to hide them everywhere."
                " Read more about permission levels {2}."
            ).format(comma_and(exposed, add_quotes=False), link, docs)
        frappe.msgprint(text, title=_("Perm Levels in Helpdesk"), indicator="blue")

    # show toast only when child table in ticket template is changed
    def rows_changed(self) -> bool:
        previous = self.get_doc_before_save()
        return not previous or self.row_values() != previous.row_values()

    def row_values(self) -> list[tuple]:
        return [
            (f.fieldname, f.visible_to, f.required, f.url_method, f.placeholder)
            for f in self.fields
        ]

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
        get_template_hidden_fields.clear_cache()
        capture_event("ticket_template_updated")

    def on_trash(self):
        self.prevent_default_delete()

    def prevent_default_delete(self):
        if self.name == DEFAULT_TICKET_TEMPLATE:
            text = _("Default template can not be deleted")
            frappe.throw(text, frappe.PermissionError)

    def before_rename(self, old_name, new_name, merge=False):
        # every visible_to lookup finds this template by name, so renaming it
        # turns field visibility off without saying so
        if old_name == DEFAULT_TICKET_TEMPLATE:
            text = _("Default template can not be renamed")
            frappe.throw(text, frappe.PermissionError)
