# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.custom.doctype.property_setter.property_setter import make_property_setter
from frappe.model.document import Document

from helpdesk.consts import DEFAULT_TICKET_TEMPLATE
from helpdesk.utils import capture_event

# fields hidden from the customer are readable by agents and above only
HIDDEN_FIELD_PERMLEVEL = 8


class HDTicketTemplate(Document):
    def validate(self):
        self.verify_field_exists()
        self.validate_unallowed_fields()

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

    def custom_field_exists(self, fieldname: str):
        return frappe.db.exists(
            {
                "doctype": "Custom Field",
                "fieldname": fieldname,
                "dt": "HD Ticket",
            }
        )

    def on_update(self):
        self.sync_field_permlevels()
        capture_event("ticket_template_updated")

    def sync_field_permlevels(self):
        """Template visibility drives HD Ticket field permlevels: hidden
        fields turn agent-only, visible fields turn customer-writable."""
        meta = frappe.get_meta("HD Ticket")
        changed = False
        for f in self.fields:
            target = HIDDEN_FIELD_PERMLEVEL if f.hide_from_customer else 0
            field = meta.get_field(f.fieldname)
            if not field or field.permlevel == target:
                continue
            self.set_field_permlevel(f.fieldname, target)
            changed = True
        if changed:
            frappe.clear_cache(doctype="HD Ticket")

    def set_field_permlevel(self, fieldname: str, level: int):
        if self.custom_field_exists(fieldname):
            frappe.db.set_value(
                "Custom Field",
                {"dt": "HD Ticket", "fieldname": fieldname},
                "permlevel",
                level,
            )
        else:
            make_property_setter("HD Ticket", fieldname, "permlevel", level, "Int")

    def on_trash(self):
        self.prevent_default_delete()

    def prevent_default_delete(self):
        if self.name == DEFAULT_TICKET_TEMPLATE:
            text = _("Default template can not be deleted")
            frappe.throw(text, frappe.PermissionError)
