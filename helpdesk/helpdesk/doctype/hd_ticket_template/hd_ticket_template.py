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
        """A field a customer cannot fill may be listed for the agent form,
        never shown to customers: showing it offers an input whose value the
        server would throw away."""
        for f in self.fields:
            if not f.fieldname or f.hide_from_customer:
                continue
            if self.custom_field_exists(f.fieldname):
                continue
            if f.fieldname in SERVER_COMPUTED_FIELDS:
                text = _(
                    "Field `{0}` is set by the system and cannot be shown to customers"
                ).format(f.fieldname)
                frappe.throw(text)
            if self.shipped_permlevel(f.fieldname) >= TICKET_INTERNAL_FIELD_PERMLEVEL:
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
        # the default template is the single source of truth for permlevels;
        # other templates are display-only
        if self.name == DEFAULT_TICKET_TEMPLATE:
            self.sync_custom_field_permlevels()
        capture_event("ticket_template_updated")

    def sync_custom_field_permlevels(self):
        """Give the site's own fields the visibility this template asks for.

        Only custom fields. A custom field's permlevel is its own definition,
        so writing it here settles the question outright. Standard fields keep
        the level the app ships, which is why nothing else in helpdesk has to
        undo anything later.

        A field dropped from the template keeps the level it had: removing a
        row must never hand customers something they could not see before.
        """
        moved = False
        for f in self.fields:
            if not self.custom_field_exists(f.fieldname):
                continue
            target = (
                TICKET_INTERNAL_FIELD_PERMLEVEL
                if f.hide_from_customer
                else TICKET_VISIBLE_FIELD_PERMLEVEL
            )
            name = frappe.db.get_value(
                "Custom Field", {"dt": "HD Ticket", "fieldname": f.fieldname}
            )
            if frappe.db.get_value("Custom Field", name, "permlevel") == target:
                continue
            frappe.db.set_value("Custom Field", name, "permlevel", target)
            moved = True
        if moved:
            frappe.clear_cache(doctype="HD Ticket")

    def shipped_permlevel(self, fieldname: str) -> int:
        """The level HD Ticket currently gives this field.

        Read from the live meta rather than the shipped DocField row, so a
        field an administrator moved through Customize Form is recognised.
        """
        field = frappe.get_meta("HD Ticket").get_field(fieldname)
        return field.permlevel if field else 0

    def on_trash(self):
        self.prevent_default_delete()

    def prevent_default_delete(self):
        if self.name == DEFAULT_TICKET_TEMPLATE:
            text = _("Default template can not be deleted")
            frappe.throw(text, frappe.PermissionError)
