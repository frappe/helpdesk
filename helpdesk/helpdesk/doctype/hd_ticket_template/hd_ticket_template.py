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
        self.warn_about_unprotected_hidden_fields()

    def warn_about_unprotected_hidden_fields(self):
        """Hiding only removes a field from the customer form. Custom field
        permlevels stay under the administrator's control, so point out the
        hidden fields the API still exposes."""
        hidden = [f.fieldname for f in self.fields if f.hide_from_customer]
        if not hidden:
            return
        unprotected = frappe.get_all(
            "Custom Field",
            filters={"dt": "HD Ticket", "fieldname": ["in", hidden], "permlevel": 0},
            pluck="label",
        )
        if not unprotected:
            return
        frappe.msgprint(
            _(
                "Hiding removes these fields from the customer form, but"
                " customers can still read and write them through the API:"
                " {0}. To protect them, set a permission level on the custom"
                " field in Customize Form."
            ).format(", ".join(unprotected)),
            title=_("Hidden fields are not protected"),
            indicator="orange",
        )

    def on_trash(self):
        self.prevent_default_delete()

    def prevent_default_delete(self):
        if self.name == DEFAULT_TICKET_TEMPLATE:
            text = _("Default template can not be deleted")
            frappe.throw(text, frappe.PermissionError)
