# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from helpdesk.consts import DEFAULT_TICKET_TEMPLATE
from helpdesk.utils import capture_event


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
        capture_event("ticket_template_updated")
        self.sync_custom_field_permlevels()

    def sync_custom_field_permlevels(self):
        """Hidden fields rise to permlevel 2 (customers can neither read nor
        write); fields no longer hidden in any template drop back to 0."""
        if not self.fields:
            return
        custom_fields = frappe.get_all(
            "Custom Field",
            filters={
                "dt": "HD Ticket",
                "fieldname": ["in", [f.fieldname for f in self.fields]],
            },
            fields=["name", "fieldname", "permlevel"],
        )
        hidden = {f.fieldname for f in self.fields if f.hide_from_customer}
        changed = False
        for custom_field in custom_fields:
            if custom_field.fieldname in hidden:
                if custom_field.permlevel < 2:
                    frappe.db.set_value(
                        "Custom Field", custom_field.name, "permlevel", 2
                    )
                    changed = True
            elif custom_field.permlevel == 2 and not self.hidden_in_another_template(
                custom_field.fieldname
            ):
                frappe.db.set_value("Custom Field", custom_field.name, "permlevel", 0)
                changed = True
        if changed:
            frappe.clear_cache(doctype="HD Ticket")

    def hidden_in_another_template(self, fieldname: str) -> bool:
        return bool(
            frappe.db.exists(
                "HD Ticket Template Field",
                {
                    "fieldname": fieldname,
                    "hide_from_customer": 1,
                    "parent": ["!=", self.name],
                },
            )
        )

    def on_trash(self):
        self.prevent_default_delete()

    def prevent_default_delete(self):
        if self.name == DEFAULT_TICKET_TEMPLATE:
            text = _("Default template can not be deleted")
            frappe.throw(text, frappe.PermissionError)
