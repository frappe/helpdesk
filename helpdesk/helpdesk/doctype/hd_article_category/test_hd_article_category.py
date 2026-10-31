# Copyright (c) 2021, Frappe Technologies and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.api.knowledge_base import create_category
from helpdesk.api.onboarding import get_general_category_id
from helpdesk.helpdesk.doctype.hd_article_category.hd_article_category import (
    add_node,
    get_branch,
    get_parent,
    get_subcategories,
    get_tree_nodes,
)
from helpdesk.patches import hd_article_category_tree
from helpdesk.test_utils import (
    category_range,
    make_article,
    make_article_category,
    make_subcategory,
    misplaced_categories,
    unique_name,
)


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
    def test_a_category_cannot_be_its_own_parent(self):
        category = make_article_category(unique_name("Self"))
        with self.assertRaises(frappe.ValidationError):
            category.update({"parent_article_category": category.name}).save()

    def test_a_subcategory_cannot_get_subcategories(self):
        parent = make_article_category(unique_name("Parent"))
        sub = make_subcategory(parent.name)
        with self.assertRaises(frappe.ValidationError):
            make_subcategory(sub.name)

    def test_a_category_with_subcategories_cannot_get_a_parent(self):
        parent = make_article_category(unique_name("Parent"))
        make_subcategory(parent.name)
        other = make_article_category(unique_name("Other"))
        with self.assertRaises(frappe.ValidationError):
            parent.update({"parent_article_category": other.name}).save()

    def test_general_cannot_become_a_subcategory(self):
        parent = make_article_category(unique_name("Parent"))
        general = frappe.get_doc("HD Article Category", get_general_category_id())
        with self.assertRaises(frappe.ValidationError):
            general.update({"parent_article_category": parent.name}).save()

    def test_general_can_hold_subcategories(self):
        sub = make_subcategory(get_general_category_id())
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
            make_subcategory(parent.name, pinned=1, pinned_order=1)
        sub = make_subcategory(parent.name)
        with self.assertRaises(frappe.ValidationError):
            sub.update({"pinned": 1, "pinned_order": 1}).save()

    def test_the_branch_is_the_category_then_its_subcategories(self):
        parent = make_article_category(unique_name("Parent"))
        sub_b = make_subcategory(parent.name, "B")
        sub_a = make_subcategory(parent.name, "A")
        self.assertEqual(get_subcategories(parent.name), [sub_a.name, sub_b.name])
        self.assertEqual(get_branch(parent.name), [parent.name, sub_a.name, sub_b.name])
        self.assertEqual(get_parent(sub_a.name), parent.name)
        self.assertIsNone(get_parent(parent.name))


class TestCategoryTree(IntegrationTestCase):
    def setUp(self):
        self.parent = make_article_category(unique_name("Tree Parent")).name
        self.sub = make_subcategory(self.parent).name
        # a parent keeps content when its Subcategory leaves
        make_article(category=self.parent)

    def ranges(self) -> dict[str, tuple[int, int]]:
        return {
            row.name: (row.lft, row.rgt)
            for row in frappe.get_all(
                "HD Article Category", fields=["name", "lft", "rgt"]
            )
        }

    def is_group(self, name) -> int:
        return frappe.db.get_value("HD Article Category", name, "is_group")

    def assertNests(self, child, parent):
        (parent_lft, parent_rgt), (lft, rgt) = category_range(parent), category_range(
            child
        )
        self.assertTrue(parent_lft < lft < rgt < parent_rgt)

    def test_a_subcategory_nests_inside_its_parent(self):
        self.assertNests(self.sub, self.parent)
        self.assertEqual((self.is_group(self.parent), self.is_group(self.sub)), (1, 0))
        self.assertEqual(misplaced_categories(), [])

    def test_reparenting_moves_the_subcategory_range(self):
        other = make_article_category(unique_name("Tree Other")).name
        make_article(category=other)
        doc = frappe.get_doc("HD Article Category", self.sub)
        doc.update({"parent_article_category": other}).save()

        self.assertNests(self.sub, other)
        self.assertEqual(misplaced_categories(), [])

        doc.update({"parent_article_category": None}).save()

        self.assertEqual(self.is_group(self.sub), 1)
        self.assertEqual(misplaced_categories(), [])

    def test_deleting_a_category_promotes_its_subcategories_in_the_tree(self):
        frappe.delete_doc("HD Article Category", self.parent)

        self.assertEqual(self.is_group(self.sub), 1)
        self.assertEqual(misplaced_categories(), [])

    def test_deleting_a_subcategory_keeps_the_tree(self):
        frappe.delete_doc("HD Article Category", self.sub)

        self.assertEqual(misplaced_categories(), [])

    def test_the_patch_rebuilds_a_stale_tree_and_is_idempotent(self):
        frappe.db.set_value(
            "HD Article Category",
            {"name": ["in", [self.parent, self.sub]]},
            {"lft": 0, "rgt": 0, "is_group": 0, "old_parent": None},
        )

        hd_article_category_tree.execute()
        ranges = self.ranges()
        hd_article_category_tree.execute()

        self.assertEqual(self.ranges(), ranges)
        self.assertNests(self.sub, self.parent)
        self.assertEqual((self.is_group(self.parent), self.is_group(self.sub)), (1, 0))
        self.assertEqual(
            frappe.db.get_value("HD Article Category", self.sub, "old_parent"),
            self.parent,
        )
        self.assertEqual(misplaced_categories(), [])

    def test_the_tree_view_adds_a_top_level_category_or_a_subcategory(self):
        top = add_node(category_name=unique_name("Tree Top"), is_root="true")
        sub = add_node(
            category_name=unique_name("Tree Sub"), parent=self.parent, is_root="false"
        )

        self.assertIsNone(get_parent(top["category"]))
        self.assertEqual(get_parent(sub["category"]), self.parent)
        # a starter article, so the new category shows in the lists
        for added in (top, sub):
            self.assertEqual(
                frappe.db.get_value("HD Article", added["article"], "category"),
                added["category"],
            )

    def test_the_tree_view_keeps_the_category_rules(self):
        sub = add_node(category_name=unique_name("Tree Sub"), parent=self.parent)
        with self.assertRaises(frappe.ValidationError):
            add_node(category_name=unique_name("Tree Deep"), parent=sub["category"])
        with self.assertRaises(frappe.ValidationError):
            add_node(category_name="General", is_root="true")

    def test_the_tree_lists_categories_by_name(self):
        prefix = unique_name("Tree Sort")
        late = make_article_category(f"{prefix} b").name
        early = make_article_category(f"{prefix} A").name
        late_sub = make_subcategory(self.parent, "b").name
        early_sub = make_subcategory(self.parent, "A").name

        roots = [row.value for row in get_tree_nodes("HD Article Category")]
        children = get_tree_nodes("HD Article Category", parent=self.parent)

        self.assertLess(roots.index(early), roots.index(late))
        self.assertNotIn(self.sub, roots)
        self.assertEqual(
            [row.value for row in children if row.value != self.sub],
            [early_sub, late_sub],
        )
        self.assertEqual(
            {row.value: row.expandable for row in children},
            dict.fromkeys([self.sub, early_sub, late_sub], 0),
        )
