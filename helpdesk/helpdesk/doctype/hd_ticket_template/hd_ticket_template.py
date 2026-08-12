# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import click
import frappe
from frappe import _
from frappe.custom.doctype.property_setter.property_setter import make_property_setter
from frappe.model.document import Document

from helpdesk.consts import (
    DEFAULT_TICKET_TEMPLATE,
    TICKET_INTERNAL_FIELD_PERMLEVEL,
    TICKET_VISIBLE_FIELD_PERMLEVEL,
)
from helpdesk.utils import capture_event


class HDTicketTemplate(Document):
    def validate(self):
        self.verify_field_exists()
        self.validate_unallowed_fields()
        self.validate_internal_fields_stay_hidden()

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

    def validate_internal_fields_stay_hidden(self):
        """An internal standard field may be listed for the agent form,
        never shown to customers."""
        for f in self.fields:
            if not f.fieldname or f.hide_from_customer:
                continue
            if self.custom_field_exists(f.fieldname):
                continue
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
            self.sync_field_permlevels()
            self.release_removed_fields()
        capture_event("ticket_template_updated")

    def sync_field_permlevels(self):
        """Hidden fields become internal: agents only. Visible fields go
        back to the level the app ships them with (visible custom fields
        to level 7). The template never lowers a field, so customers may
        fill visible fields while creating a ticket but never edit them
        afterwards."""
        meta = frappe.get_meta("HD Ticket")
        changed = []
        for f in self.fields:
            field = meta.get_field(f.fieldname)
            if not field:
                continue
            target = self.target_permlevel(f)
            if field.permlevel == target:
                continue
            self.set_field_permlevel(f.fieldname, target)
            hidden = target == TICKET_INTERNAL_FIELD_PERMLEVEL
            state = "hidden from customers" if hidden else "visible to customers"
            changed.append(f"{f.fieldname} ({state})")
        if changed:
            frappe.clear_cache(doctype="HD Ticket")
            self.warn_permlevel_changes(changed)

    def target_permlevel(self, field_row) -> int:
        if field_row.hide_from_customer:
            return TICKET_INTERNAL_FIELD_PERMLEVEL
        if self.custom_field_exists(field_row.fieldname):
            return TICKET_VISIBLE_FIELD_PERMLEVEL
        return self.shipped_permlevel(field_row.fieldname)

    def release_removed_fields(self):
        """A standard field removed from the default template goes back to
        the level the app ships it with. Custom fields have no shipped
        level, so their level is left to the admin."""
        previous = self.get_doc_before_save()
        if not previous:
            return
        current = {f.fieldname for f in self.fields}
        removed = [
            f.fieldname
            for f in previous.fields
            if f.fieldname and f.fieldname not in current
        ]
        self.restore_shipped_permlevels(removed)

    def restore_shipped_permlevels(self, fieldnames: list[str]):
        """Delete the stored level override so the level from the app's
        field definition applies again — standard fields only."""
        restored = []
        for fieldname in fieldnames:
            if self.custom_field_exists(fieldname):
                continue
            if not self.delete_permlevel_property_setter(fieldname):
                continue
            restored.append(f"{fieldname} (back to default)")
        if restored:
            frappe.clear_cache(doctype="HD Ticket")
            self.warn_permlevel_changes(restored)

    def delete_permlevel_property_setter(self, fieldname: str) -> bool:
        filters = {
            "doc_type": "HD Ticket",
            "field_name": fieldname,
            "property": "permlevel",
        }
        if not frappe.db.exists("Property Setter", filters):
            return False
        frappe.db.delete("Property Setter", filters)
        return True

    def shipped_permlevel(self, fieldname: str) -> int:
        return (
            frappe.db.get_value(
                "DocField", {"parent": "HD Ticket", "fieldname": fieldname}, "permlevel"
            )
            or 0
        )

    def warn_permlevel_changes(self, changed: list[str]):
        if frappe.flags.in_patch or frappe.flags.in_migrate:
            for line in changed:
                click.secho(f"{self.name} template: {line}", fg="yellow")
            return
        docs_link = (
            "<a href='https://docs.frappe.io/framework/user/en/basics/"
            "users-and-permissions' target='_blank'>Users and Permissions</a>"
        )
        frappe.msgprint(
            _(
                "Saving this template changed what customers can do with these "
                "ticket fields: {0}. This overrides anything set in Customize "
                "Form. See {1}."
            ).format(", ".join(changed), docs_link),
            title=_("Customer access updated"),
            indicator="yellow",
        )

    def set_field_permlevel(self, fieldname: str, level: int):
        if self.custom_field_exists(fieldname):
            frappe.db.set_value(
                "Custom Field",
                {"dt": "HD Ticket", "fieldname": fieldname},
                "permlevel",
                level,
            )
        elif level == self.shipped_permlevel(fieldname):
            # same as the shipped level: no override needed, drop any old one
            self.delete_permlevel_property_setter(fieldname)
        else:
            make_property_setter("HD Ticket", fieldname, "permlevel", level, "Int")

    def on_trash(self):
        self.prevent_default_delete()

    def prevent_default_delete(self):
        if self.name == DEFAULT_TICKET_TEMPLATE:
            text = _("Default template can not be deleted")
            frappe.throw(text, frappe.PermissionError)
