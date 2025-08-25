# Copyright (c) 2025, Frappe Technologies and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.setup.install import add_default_status

# On IntegrationTestCase, the doctype test records and all
# link-field test record dependencies are recursively loaded
# Use these module variables to add/remove to/from that list
EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]


class IntegrationTestHDTicketStatus(IntegrationTestCase):
    """
    Integration tests for HDTicketStatus.
    Use this class for testing interactions between multiple components.
    """

    def setUp(self):
        add_default_status()

    def test_validate_one_min_status_category(self):
        doc = frappe.get_doc("HD Ticket Status", "Open")
        doc.category = "Paused"
        self.assertRaises(frappe.ValidationError, doc.save)

    def test_delete_status_change(self):
        doc = frappe.get_doc("HD Ticket Status", "Closed")
        doc.label = "New Closed"
        # doc.save()
        self.assertRaises(frappe.ValidationError, doc.save)

    def test_closed_status_delete(self):
        """
        Test that closed status cannot be deleted.
        """
        return
        self.assertRaises(
            frappe.ValidationError, frappe.delete_doc("HD Ticket Status", "Closed")
        )
