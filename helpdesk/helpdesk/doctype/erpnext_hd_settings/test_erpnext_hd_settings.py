# Copyright (c) 2026, Frappe Technologies and Contributors
# See license.txt

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

# On IntegrationTestCase, the doctype test records and all
# link-field test record dependencies are recursively loaded
# Use these module variables to add/remove to/from that list
EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]


class IntegrationTestERPNextHDSettings(IntegrationTestCase):
    """
    Integration tests for ERPNextHDSettings.
    Use this class for testing interactions between multiple components.
    """

    @patch("frappe.get_installed_apps", return_value=["frappe", "helpdesk", "erpnext"])
    def test_validate_with_erpnext_installed(self, mock_get_installed_apps):
        settings_doc = frappe.get_single("ERPNext HD Settings")
        settings_doc.enabled = 1
        try:
            settings_doc.save()
        except Exception as e:
            self.fail(f"Validation failed when ERPNext is installed: {e}")

    # TODO: Make this test case work
    # @patch("frappe.get_installed_apps", return_value=["frappe", "helpdesk"])
    # def test_validate_without_erpnext_installed(self, mock_get_installed_apps):
    #     settings_doc = frappe.get_single("ERPNext HD Settings")
    #     settings_doc.enabled = 1
    #     with self.assertRaises(frappe.ValidationError) as context:
    #         settings_doc.validate()
    #     self.assertIn(
    #         "ERPNext is not installed on your site. Please install ERPNext to enable this setting.",
    #         str(context.exception),
    #     )
