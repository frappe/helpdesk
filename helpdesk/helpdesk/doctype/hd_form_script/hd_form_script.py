# Copyright (c) 2024, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from helpdesk.api.settings.field_dependency import handle_form_customization


class HDFormScript(Document):
    # ON TRASH
    def on_trash(self):
        # check if the name has "Field Dependency" in it
        if "Field Dependency" not in self.name:
            return
        child_field = self.name.split("-")[-1]
        if not child_field:
            return
        handle_form_customization(child_field, None, None)


def get_form_script(
    dt,
    apply_to="Form",
    is_customer_portal=False,
    new_page=False,
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
        return [d.script for d in doc] if len(doc) > 1 else doc[0].script
    else:
        return None
