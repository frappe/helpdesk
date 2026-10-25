# Copyright (c) 2021, Frappe Technologies and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.api.knowledge_base import create_category
from helpdesk.api.onboarding import get_general_category_id
from helpdesk.helpdesk.doctype.hd_article_category.hd_article_category import (
    get_branch,
    get_parent,
    get_subcategories,
)
from helpdesk.test_utils import make_article_category, unique_name


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


class TestSubcategory(IntegrationTestCase):
    def make_subcategory(self, parent: str, label: str = "Sub", **values):
        return make_article_category(
            unique_name(label), parent_article_category=parent, **values
        )

    def test_a_category_cannot_be_its_own_parent(self):
        category = make_article_category(unique_name("Self"))
        with self.assertRaises(frappe.ValidationError):
            category.update({"parent_article_category": category.name}).save()

    def test_a_subcategory_cannot_get_subcategories(self):
        parent = make_article_category(unique_name("Parent"))
        sub = self.make_subcategory(parent.name)
        with self.assertRaises(frappe.ValidationError):
            self.make_subcategory(sub.name)

    def test_a_category_with_subcategories_cannot_get_a_parent(self):
        parent = make_article_category(unique_name("Parent"))
        self.make_subcategory(parent.name)
        other = make_article_category(unique_name("Other"))
        with self.assertRaises(frappe.ValidationError):
            parent.update({"parent_article_category": other.name}).save()

    def test_general_cannot_become_a_subcategory(self):
        parent = make_article_category(unique_name("Parent"))
        general = frappe.get_doc("HD Article Category", get_general_category_id())
        with self.assertRaises(frappe.ValidationError):
            general.update({"parent_article_category": parent.name}).save()

    def test_general_can_hold_subcategories(self):
        sub = self.make_subcategory(get_general_category_id())
        self.assertEqual(get_parent(sub.name), get_general_category_id())

    def test_a_pinned_category_is_unpinned_when_it_gets_a_parent(self):
        parent = make_article_category(unique_name("Parent"))
        doc = make_article_category(unique_name("Pinned"), pinned=1, pinned_order=1)
        doc.update({"parent_article_category": parent.name}).save()
        self.assertEqual((doc.pinned, doc.pinned_order), (0, 0))
        self.assertTrue(doc.flags.unpinned)

    def test_a_subcategory_cannot_be_pinned(self):
        parent = make_article_category(unique_name("Parent"))
        with self.assertRaises(frappe.ValidationError):
            self.make_subcategory(parent.name, pinned=1, pinned_order=1)
        sub = self.make_subcategory(parent.name)
        with self.assertRaises(frappe.ValidationError):
            sub.update({"pinned": 1, "pinned_order": 1}).save()

    def test_the_branch_is_the_category_then_its_subcategories(self):
        parent = make_article_category(unique_name("Parent"))
        sub_b = self.make_subcategory(parent.name, "B")
        sub_a = self.make_subcategory(parent.name, "A")
        self.assertEqual(get_subcategories(parent.name), [sub_a.name, sub_b.name])
        self.assertEqual(get_branch(parent.name), [parent.name, sub_a.name, sub_b.name])
        self.assertEqual(get_parent(sub_a.name), parent.name)
        self.assertIsNone(get_parent(parent.name))
