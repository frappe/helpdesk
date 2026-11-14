# Copyright (c) 2026, Frappe Technologies and Contributors
# See license.txt

from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

# On IntegrationTestCase, the doctype test records and all
# link-field test record dependencies are recursively loaded
# Use these module variables to add/remove to/from that list
EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]


class IntegrationTestERPNextHDSettings(FrappeTestCase):
    """
    Integration tests for ERPNextHDSettings.
    Use this class for testing interactions between multiple components.
    """

    def test_validate_with_erpnext_installed(self):
        # keep the real apps so their wildcard doc_events (e.g. the whatsapp app) still resolve
        installed_apps = [*frappe.get_installed_apps(), "erpnext"]
        settings_doc = frappe.get_single("ERPNext HD Settings")
        settings_doc.enabled = 1
        with patch("frappe.get_installed_apps", return_value=installed_apps):
            try:
                settings_doc.save()
            except Exception as e:
                self.fail(f"Validation failed when ERPNext is installed: {e}")
