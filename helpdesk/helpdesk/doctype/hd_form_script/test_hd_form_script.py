# Copyright (c) 2024, Frappe Technologies and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from helpdesk.test_utils import create_field_dependency

DEPENDENCY_NAME = "Field Dependency-ticket_type-priority"
PARENT_FIELD = "ticket_type"
CHILD_FIELD = "priority"


class TestHDFormScript(FrappeTestCase):
    def setUp(self):
        # Set up any necessary test data or state
        create_field_dependency()
        pass

    def test_field_dependency_naming(self):
        # if we call this method, is the name of doc in the format "Field Dependency-{parent_field}-{child_field}"?
        dep_doc = frappe.get_list("HD Form Script", fields=["name", "is_standard"])[0]
        self.assertEqual(
            dep_doc.name,
            DEPENDENCY_NAME,
            f"Dependency name should be {DEPENDENCY_NAME}",
        )
        self.assertEqual(dep_doc.is_standard, 1)

    # test to check whether form customization is created or not
    def test_field_dependency_form_customization(self):

        # check if form customization is applied
        field = get_customized_form_field()
        self.assertEqual(field.depends_on, f"eval:doc.{PARENT_FIELD} != ''")
        self.assertEqual(
            field.mandatory_depends_on,
            f"eval:['Question', 'Bug'].includes(doc.{PARENT_FIELD})",
        )

    def test_field_dependency_enable_toggle(self):
        # If we disable a field dependency, does it remove the form customization?
        doc = frappe.get_doc("HD Form Script", DEPENDENCY_NAME)
        doc.enabled = 0
        doc.save()
        field = get_customized_form_field()
        self.assertIsNone(field.depends_on, "Depends on should be None when disabled")
        self.assertIsNone(
            field.mandatory_depends_on,
            "Mandatory depends on should be None when disabled",
        )

    def test_field_dependency_deletion(self):
        # If we delete a field dependency, does it remove the form customization?
        doc = frappe.get_doc("HD Form Script", DEPENDENCY_NAME)
        frappe.delete_doc("HD Form Script", doc.name)
        field = get_customized_form_field()
        self.assertIsNone(field.depends_on, "Depends on should be None after deletion")
        self.assertIsNone(
            field.mandatory_depends_on,
            "Mandatory depends on should be None after deletion",
        )

    def tearDown(self):
        frappe.db.delete(
            "HD Form Script", {"name": "Field Dependency-ticket_type-priority"}
        )
        pass


def get_customized_form_field():
    """
    Returns the customized form field for HD Ticket.
    """
    cf = frappe.get_doc("Customize Form")
    cf.doc_type = "HD Ticket"
    cf.fetch_to_customize()
    f = [f for f in cf.fields if f.fieldname == CHILD_FIELD]
    return f[0] if f else None
