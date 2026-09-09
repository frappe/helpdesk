# Copyright (c) 2026, Frappe Technologies and Contributors
# See license.txt

from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from helpdesk.setup.install import add_default_agent_status
from helpdesk.test_utils import (
    make_agent,
    make_agent_status,
    set_agent_availability,
    set_agent_status_enabled,
    set_default_agent_status,
)


class TestHDAgentStatus(FrappeTestCase):
    """Integration tests for HD Agent Status."""

    DEFAULT_STATUSES = ("Active", "Away", "Unavailable")

    def setUp(self):
        # start from the shipped defaults (Active / Away / Unavailable)
        add_default_agent_status()

    def tearDown(self):
        # delete statuses created by tests, keep the shipped ones
        frappe.db.delete("HD Agent Status", {"name": ["not in", self.DEFAULT_STATUSES]})
        # db.delete skips link checks, re-seed so the default always exists
        add_default_agent_status()

    def _use_default(self, status: str):
        """Set a different default for this test, restores it after."""
        current = frappe.db.get_single_value("HD Settings", "default_agent_status")
        set_default_agent_status(status)
        self.addCleanup(set_default_agent_status, current)

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

        self.assertEqual(
            frappe.db.get_single_value("HD Settings", "default_agent_status"), "Active"
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

    # the default status cannot be disabled
    def test_default_status_cannot_be_disabled(self):
        active = frappe.get_doc("HD Agent Status", "Active")
        active.enabled = 0
        with self.assertRaises(frappe.ValidationError):
            active.save()

    # any other status can be disabled, Active category or not
    def test_non_default_status_can_be_disabled(self):
        online = make_agent_status("Online", category="Active")
        online.enabled = 0
        online.save()
        self.assertFalse(online.enabled)

    # agents get moved to the default, else their picker goes blank
    def test_disabling_status_resets_agents_to_default(self):
        focusing = make_agent_status("Focusing", category="Away")
        agent = make_agent("disable_status@test.com", first_name="Disable Status")
        set_agent_availability(agent, "Focusing")

        focusing.enabled = 0
        focusing.save()

        self.assertEqual(
            frappe.db.get_value("HD Agent", agent, "availability"), "Active"
        )

    # the reset runs through HD Agent, so every connected client hears about it
    def test_disabling_status_publishes_for_each_agent(self):
        focusing = make_agent_status("Focusing", category="Away")
        first = make_agent("disable_publish_1@test.com", first_name="Disable Publish 1")
        second = make_agent(
            "disable_publish_2@test.com", first_name="Disable Publish 2"
        )
        set_agent_availability(first, "Focusing")
        set_agent_availability(second, "Focusing")

        with patch(
            "helpdesk.helpdesk.doctype.hd_agent.hd_agent.publish_event"
        ) as publish:
            focusing.enabled = 0
            focusing.save()

        self.assertEqual(publish.call_count, 2)
        self.assertEqual(
            {call.kwargs["data"]["agent"] for call in publish.call_args_list},
            {first, second},
        )

    # only agents on the disabled status are touched
    def test_disabling_status_leaves_other_agents_alone(self):
        online = make_agent_status("Online", category="Active")
        agent = make_agent("unused_status@test.com", first_name="Unused Status")
        set_agent_availability(agent, "Away")

        online.enabled = 0
        online.save()

        self.assertEqual(frappe.db.get_value("HD Agent", agent, "availability"), "Away")

    # category doesn't decide the default anymore, changing it is fine
    def test_status_can_be_demoted(self):
        online = make_agent_status("Online", category="Active")
        online.category = "Away"
        online.save()
        self.assertEqual(online.category, "Away")

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
        # frappe rewrites link fields on Singles too, so the setting follows
        self.assertEqual(
            frappe.db.get_single_value("HD Settings", "default_agent_status"), "Online"
        )

    # can't delete the default, even force delete (that only skips the link check)
    def test_default_status_cannot_be_deleted(self):
        with self.assertRaises(frappe.ValidationError):
            frappe.delete_doc("HD Agent Status", "Active")
        with self.assertRaises(frappe.ValidationError):
            frappe.delete_doc("HD Agent Status", "Active", force=True)

    # any other status can be deleted
    def test_non_default_status_can_be_deleted(self):
        make_agent_status("Online", category="Active")
        frappe.delete_doc("HD Agent Status", "Online")
        self.assertFalse(frappe.db.exists("HD Agent Status", "Online"))

    # agents move to the status set in HD Settings, not whatever the db returns first
    def test_agents_move_to_the_configured_default(self):
        self._use_default("Away")
        focusing = make_agent_status("Focusing", category="Away")
        agent = make_agent("configured_default@test.com", first_name="Configured")
        set_agent_availability(agent, "Focusing")

        focusing.enabled = 0
        focusing.save()

        self.assertEqual(frappe.db.get_value("HD Agent", agent, "availability"), "Away")

    # new agents start on the chosen default, not just any Active status
    def test_new_agent_uses_the_configured_default(self):
        self._use_default("Away")

        agent = make_agent("new_agent_default@test.com", first_name="New Default")

        self.assertEqual(frappe.db.get_value("HD Agent", agent, "availability"), "Away")

    # the patch keeps whatever default the site was already using
    def test_patch_picks_the_status_the_old_lookup_returned(self):
        from helpdesk.patches.set_default_agent_status_in_settings import (
            execute as name_the_default,
        )

        # "Online" is newer than "Active", so the old query would have picked it
        make_agent_status("Online", category="Active")
        set_default_agent_status(None)
        self.addCleanup(set_default_agent_status, "Active")

        name_the_default()

        self.assertEqual(
            frappe.db.get_single_value("HD Settings", "default_agent_status"), "Online"
        )

    # a default disabled via db can still save other fields
    def test_disabled_default_can_still_save_unrelated_fields(self):
        focusing = make_agent_status("Focusing", category="Away")
        self._use_default("Focusing")
        set_agent_status_enabled("Focusing", 0)

        focusing.reload()
        focusing.color = "Blue"
        focusing.save()

        self.assertEqual(
            frappe.db.get_value("HD Agent Status", "Focusing", "color"), "Blue"
        )

    # disabling a status nobody is on works even with no default set
    def test_disabling_an_unheld_status_needs_no_default(self):
        focusing = make_agent_status("Focusing", category="Away")
        self._use_default(None)

        focusing.enabled = 0
        focusing.save()

        self.assertFalse(focusing.enabled)

    # HD Settings refuses a disabled status as the default
    def test_hd_settings_rejects_disabled_default_status(self):
        make_agent_status("Focusing", category="Away", enabled=0)

        settings = frappe.get_doc("HD Settings")
        settings.default_agent_status = "Focusing"
        with self.assertRaises(frappe.ValidationError):
            settings.save()
