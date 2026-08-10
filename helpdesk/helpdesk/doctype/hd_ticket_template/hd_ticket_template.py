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
        """Raise custom fields hidden from customers to permlevel 2 so they
        can neither read nor write them.

        Fail-closed: the permlevel is never lowered automatically, because
        the raise is indistinguishable from an administrator protecting the
        field independently. Unhiding only notifies, and exposing the field
        again is an explicit Customize Form action."""
        hidden = {f.fieldname for f in self.fields if f.hide_from_customer}
        if hidden:
            raised = frappe.get_all(
                "Custom Field",
                filters={
                    "dt": "HD Ticket",
                    "fieldname": ["in", list(hidden)],
                    "permlevel": ["<", 2],
                },
                pluck="name",
            )
            if raised:
                frappe.db.set_value(
                    "Custom Field", {"name": ["in", raised]}, "permlevel", 2
                )
                frappe.clear_cache(doctype="HD Ticket")
        self.warn_about_protected_fields(self.previously_hidden_fields() - hidden)

    def previously_hidden_fields(self) -> set:
        before = self.get_doc_before_save()
        if not before:
            return set()
        return {f.fieldname for f in before.fields if f.hide_from_customer}

    def warn_about_protected_fields(self, fieldnames: set):
        """Tell the administrator which fields stay invisible to customers."""
        if not fieldnames:
            return
        still_protected = frappe.get_all(
            "Custom Field",
            filters={
                "dt": "HD Ticket",
                "fieldname": ["in", list(fieldnames)],
                "permlevel": [">", 0],
            },
            pluck="label",
        )
        if not still_protected:
            return
        frappe.msgprint(
            _(
                "These fields keep their protected permlevel and stay invisible"
                " to customers: {0}. To expose them, lower the permlevel of the"
                " custom field in Customize Form."
            ).format(", ".join(still_protected)),
            title=_("Fields still protected"),
            indicator="orange",
        )

    def on_trash(self):
        self.prevent_default_delete()
        self.warn_about_protected_fields(
            {f.fieldname for f in self.fields if f.hide_from_customer}
        )

    def prevent_default_delete(self):
        if self.name == DEFAULT_TICKET_TEMPLATE:
            text = _("Default template can not be deleted")
            frappe.throw(text, frappe.PermissionError)
