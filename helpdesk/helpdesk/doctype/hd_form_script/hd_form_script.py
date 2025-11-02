# Copyright (c) 2024, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from helpdesk.api.settings.field_dependency import (
    get_fields_criteria,
    handle_fields_criteria,
    handle_form_customization,
)


class HDFormScript(Document):
    def before_save(self):
        self.handle_enabled_change()

    def handle_enabled_change(self):
        if self.is_new():
            return
        if not self.is_standard:
            return
        if not self.has_value_changed("enabled"):
            return

        if not self.enabled:
            [_, child_field] = self.get_parent_child_field()
            handle_form_customization(child_field, None, None)

        if self.enabled:
            [parent_field, child_field] = self.get_parent_child_field()
            fields_criteria = get_fields_criteria(self.script)
            handle_fields_criteria(parent_field, child_field, fields_criteria, {})

    def get_parent_child_field(self):
        """Returns the child field from the name of the document"""
        if not self.name:
            return None
        if "Field Dependency" not in self.name:
            return None

        # Assuming the name is in the format "Field Dependency-{parent_field}-{child_field}"
        parts = self.name.split("-")
        if len(parts) < 2:
            return None
        return [parts[1], parts[2]] if len(parts) > 2 else [parts[1], None]

    def on_trash(self):
        if not self.is_standard:
            return
        [_, child_field] = self.get_parent_child_field()
        if not child_field:
            return
        handle_form_customization(child_field, None, None)


def get_form_script(
    dt,
    apply_to="Form",
    is_customer_portal=False,
    apply_on_new_page=False,
):
    """Returns the form script for the given doctype"""
    FormScript = frappe.qb.DocType("HD Form Script")
    query = (
        frappe.qb.from_(FormScript)
        .select("script")
        .where(FormScript.dt == dt)
        .where(FormScript.apply_to == apply_to)
        .where(FormScript.enabled == 1)
        .where(FormScript.apply_on_new_page == apply_on_new_page)
        .where(FormScript.apply_to_customer_portal == is_customer_portal)
    )

    doc = query.run(as_dict=True)
    if doc:
        return [d.script for d in doc]
        # if len(doc) > 1 else doc[0].script
    else:
        return None
