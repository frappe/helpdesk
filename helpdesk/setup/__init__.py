"""Post-install setup for QCS features within Helpdesk."""

import os

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from helpdesk.setup.install import get_custom_fields

FORM_SCRIPT_NAME = "Helpdesk AI Support Actions"


def after_migrate():
    """Update the HD Form Script and ensure custom fields exist."""
    create_custom_fields(get_custom_fields())
    _create_form_script()


def _create_form_script():
    js_path = os.path.join(
        os.path.dirname(__file__), "..", "hd_form_scripts", "ai_support_actions.js"
    )

    if not os.path.exists(js_path):
        frappe.log_error("HD Form Script JS not found", js_path)
        return

    with open(js_path) as f:
        script_content = f.read()

    if frappe.db.exists("HD Form Script", FORM_SCRIPT_NAME):
        doc = frappe.get_doc("HD Form Script", FORM_SCRIPT_NAME)
        doc.script = script_content
        doc.enabled = 1
        doc.save(ignore_permissions=True)
        print(f"Updated HD Form Script: {FORM_SCRIPT_NAME}")
    else:
        doc = frappe.get_doc(
            {
                "doctype": "HD Form Script",
                "name": FORM_SCRIPT_NAME,
                "dt": "HD Ticket",
                "apply_to": "Form",
                "enabled": 1,
                "script": script_content,
            }
        )
        doc.insert(ignore_permissions=True)
        print(f"Created HD Form Script: {FORM_SCRIPT_NAME}")

    frappe.db.commit()
