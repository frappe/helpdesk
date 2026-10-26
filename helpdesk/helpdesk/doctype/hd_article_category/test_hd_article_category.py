# Copyright (c) 2021, Frappe Technologies and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.api.knowledge_base import create_category
from helpdesk.api.onboarding import get_general_category_id


class TestHDArticleCategory(IntegrationTestCase):
    def tearDown(self):
        frappe.db.delete(
            "HD Article Category",
            {
                "category_name": ["!=", "General"],
                "name": ["!=", get_general_category_id()],
            },
        )

    def test_rename_category_to_general_raises_error(self):
        create_category("Test Category")
        category_id = frappe.db.get_value(
            "HD Article Category", {"category_name": "Test Category"}, "name"
        )
        with self.assertRaises(frappe.ValidationError):
            doc = frappe.get_doc("HD Article Category", category_id)
            doc.category_name = "General"
            doc.save()

    def test_create_general_category_raises_error(self):
        with self.assertRaises(frappe.ValidationError):
            create_category("general")

    def test_create_general_category_case_insensitive(self):
        # "General", "GENERAL", "gEnErAl" should all fail
        for title in ["General", "GENERAL", "gEnErAl"]:
            with self.assertRaises(frappe.ValidationError):
                create_category(title)

    def test_create_general_category_with_whitespace(self):
        # "  general  " should also fail
        with self.assertRaises(frappe.ValidationError):
            create_category("  general  ")


class TestPinnedCategory(IntegrationTestCase):
    def setUp(self):
        self.category = frappe.get_doc(
            {"doctype": "HD Article Category", "category_name": "Pin Test"}
        ).insert()

    def tearDown(self):
        frappe.delete_doc("HD Article Category", self.category.name, force=True)

    def test_pinned_needs_an_order(self):
        for order in (0, -1):
            with self.subTest(order=order), self.assertRaises(frappe.ValidationError):
                self.category.update({"pinned": 1, "pinned_order": order}).save()

    def test_unpinning_clears_the_order(self):
        self.category.update({"pinned": 1, "pinned_order": 2}).save()
        self.category.update({"pinned": 0}).save()
        self.assertEqual(self.category.pinned_order, 0)
