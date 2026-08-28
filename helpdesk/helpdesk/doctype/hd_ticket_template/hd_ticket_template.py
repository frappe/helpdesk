# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from helpdesk.consts import (
    DEFAULT_TICKET_TEMPLATE,
    SERVER_COMPUTED_FIELDS,
    TICKET_INTERNAL_FIELD_PERMLEVEL,
)
from helpdesk.utils import capture_event


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
            if self.current_permlevel(f.fieldname) >= TICKET_INTERNAL_FIELD_PERMLEVEL:
                if self.custom_field_exists(f.fieldname):
                    text = _(
                        "Field `{0}` is internal and cannot be shown to customers."
                        " Lower its permission level in Customize Form to show it."
                    ).format(f.fieldname)
                else:
                    text = _(
                        "Field `{0}` is internal and cannot be shown to customers"
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
        if self.name == DEFAULT_TICKET_TEMPLATE:
            self.make_hidden_custom_fields_internal()
        capture_event("ticket_template_updated")

    def make_hidden_custom_fields_internal(self):
        """Hiding a custom field must revoke API reads, not just the form
        input. Raise only: showing a field again takes Customize Form, so a
        template save can never hand customers a field they could not read."""
        moved = False
        for f in self.fields:
            if not f.hide_from_customer or not self.custom_field_exists(f.fieldname):
                continue
            if self.current_permlevel(f.fieldname) >= TICKET_INTERNAL_FIELD_PERMLEVEL:
                continue
            frappe.db.set_value(
                "Custom Field",
                {"dt": "HD Ticket", "fieldname": f.fieldname},
                "permlevel",
                TICKET_INTERNAL_FIELD_PERMLEVEL,
            )
            moved = True
        if moved:
            frappe.clear_cache(doctype="HD Ticket")

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
