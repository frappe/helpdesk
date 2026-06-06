# Copyright (c) 2026, Frappe Technologies and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from helpdesk.setup.install import add_default_agent_status
from helpdesk.test_utils import make_agent, make_agent_status


class TestHDAgentStatus(FrappeTestCase):
    """Integration tests for HD Agent Status."""

    DEFAULT_STATUSES = ("Active", "Away", "Unavailable")

    def setUp(self):
        # starts from the install-seeded defaults (Active / Away / Unavailable).
        add_default_agent_status()

    def tearDown(self):
        # Delete only the statuses a test created or renamed (e.g. the Active ->
        # Online rename); keep the seeded defaults so other suites that rely on
        # them (e.g. HD Agent) are unaffected. setUp restores any renamed default.
        frappe.db.delete("HD Agent Status", {"name": ["not in", self.DEFAULT_STATUSES]})

    # The statuses created on install exist with the expected categories
    def test_default_statuses_are_seeded(self):
        defaults = {
            "Active": "Active",
            "Away": "Away",
            "Unavailable": "Unavailable",
        }
        for status, category in defaults.items():
            self.assertTrue(frappe.db.exists("HD Agent Status", status))
            self.assertEqual(
                frappe.db.get_value("HD Agent Status", status, "category"), category
            )

    # autoname is field:agent_status, so the record name is the status value
    def test_name_is_the_status_value(self):
        status = make_agent_status("In a Meeting", category="Away")
        self.assertEqual(status.name, "In a Meeting")

    # agent_status is unique; the same status cannot be created twice
    def test_duplicate_status_not_allowed(self):
        make_agent_status("On Lunch", category="Away")
        with self.assertRaises(frappe.DuplicateEntryError):
            make_agent_status("On Lunch", category="Away")

    # category must be one of Active / Away / Unavailable
    def test_invalid_category_rejected(self):
        with self.assertRaises(frappe.ValidationError):
            make_agent_status("Busy", category="Busy")

    # multiple statuses may use the Active category
    def test_second_active_status_allowed(self):
        status = make_agent_status("Online", category="Active")
        self.assertEqual(status.category, "Active")

    # switching another status into the Active category is allowed too
    def test_switching_status_to_active_allowed(self):
        status = make_agent_status("Focusing", category="Away")
        status.category = "Active"
        status.save()
        self.assertEqual(status.category, "Active")

    # editing the existing Active status must not trip the rule on itself
    def test_resaving_active_status_allowed(self):
        active = frappe.get_doc("HD Agent Status", "Active")
        active.status_order = 100
        active.save()  # self is excluded; must not raise
        self.assertEqual(
            frappe.db.get_value("HD Agent Status", "Active", "status_order"), 100
        )

    # category is mandatory
    def test_category_is_mandatory(self):
        with self.assertRaises(frappe.MandatoryError):
            make_agent_status("No Category", category="")

    # the last enabled Active status cannot be disabled
    def test_last_active_status_cannot_be_disabled(self):
        active = frappe.get_doc("HD Agent Status", "Active")
        active.enable = 0
        with self.assertRaises(frappe.ValidationError):
            active.save()

    # an Active status can be disabled while another enabled Active status remains
    def test_active_status_can_be_disabled_with_another_active(self):
        make_agent_status("Online", category="Active")
        active = frappe.get_doc("HD Agent Status", "Active")
        active.enable = 0
        active.save()
        self.assertFalse(active.enable)

    # the last Active status cannot be moved out of the Active category
    def test_last_active_status_cannot_be_demoted(self):
        active = frappe.get_doc("HD Agent Status", "Active")
        active.category = "Away"
        with self.assertRaises(frappe.ValidationError):
            active.save()

    # an Active status can be demoted while another enabled Active status remains
    def test_active_status_can_be_demoted_with_another_active(self):
        make_agent_status("Online", category="Active")
        active = frappe.get_doc("HD Agent Status", "Active")
        active.category = "Away"
        active.save()
        self.assertEqual(active.category, "Away")

    # the Active status can be renamed; the rename cascades to linked agents
    def test_active_status_rename_cascades_to_agents(self):
        agent = make_agent("rename_active@test.com", first_name="Rename Active")
        self.assertEqual(
            frappe.db.get_value("HD Agent", agent, "availability"), "Active"
        )

        frappe.rename_doc("HD Agent Status", "Active", "Online")

        self.assertEqual(
            frappe.db.get_value("HD Agent", agent, "availability"), "Online"
        )

    # the last Active status cannot be deleted
    def test_last_active_status_cannot_be_deleted(self):
        with self.assertRaises(frappe.ValidationError):
            frappe.delete_doc("HD Agent Status", "Active")

    # an Active status can be deleted while another enabled Active status remains
    def test_active_status_can_be_deleted_with_another_active(self):
        make_agent_status("Online", category="Active")
        frappe.delete_doc("HD Agent Status", "Active")
        self.assertFalse(frappe.db.exists("HD Agent Status", "Active"))
