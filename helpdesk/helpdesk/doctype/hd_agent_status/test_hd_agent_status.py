# Copyright (c) 2026, Frappe Technologies and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.test_utils import make_agent


class IntegrationTestHDAgentStatus(IntegrationTestCase):
    """Integration tests for HD Agent Status."""

    def _make_status(self, agent_status, category="Away", enable=1, order=None):
        return frappe.get_doc(
            {
                "doctype": "HD Agent Status",
                "agent_status": agent_status,
                "category": category,
                "enable": enable,
                "order": order,
            }
        ).insert()

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
        status = self._make_status("In a Meeting", category="Away")
        self.assertEqual(status.name, "In a Meeting")

    # agent_status is unique; the same status cannot be created twice
    def test_duplicate_status_not_allowed(self):
        self._make_status("On Lunch", category="Away")
        with self.assertRaises(frappe.DuplicateEntryError):
            self._make_status("On Lunch", category="Away")

    # category must be one of Active / Away / Unavailable
    def test_invalid_category_rejected(self):
        with self.assertRaises(frappe.ValidationError):
            self._make_status("Busy", category="Busy")

    # only one status may use the Active category (one is already seeded on install)
    def test_second_active_status_rejected(self):
        with self.assertRaises(frappe.ValidationError):
            self._make_status("Online", category="Active")

    # switching another status into the Active category is blocked too
    def test_switching_status_to_active_rejected(self):
        status = self._make_status("Focusing", category="Away")
        status.category = "Active"
        with self.assertRaises(frappe.ValidationError):
            status.save()

    # editing the existing Active status must not trip the rule on itself
    def test_resaving_active_status_allowed(self):
        active = frappe.get_doc("HD Agent Status", "Active")
        active.order = 10
        active.save()  # self is excluded; must not raise
        self.assertEqual(frappe.db.get_value("HD Agent Status", "Active", "order"), 10)

    # category is mandatory
    def test_category_is_mandatory(self):
        with self.assertRaises(frappe.MandatoryError):
            self._make_status("No Category", category="")

    # the Active status must stay enabled
    def test_active_status_cannot_be_disabled(self):
        active = frappe.get_doc("HD Agent Status", "Active")
        active.enable = 0
        with self.assertRaises(frappe.ValidationError):
            active.save()

    # the Active status cannot be moved out of the Active category
    def test_active_status_cannot_be_demoted(self):
        active = frappe.get_doc("HD Agent Status", "Active")
        active.category = "Away"
        with self.assertRaises(frappe.ValidationError):
            active.save()

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

    # the Active status cannot be deleted
    def test_active_status_cannot_be_deleted(self):
        with self.assertRaises(frappe.ValidationError):
            frappe.delete_doc("HD Agent Status", "Active")
