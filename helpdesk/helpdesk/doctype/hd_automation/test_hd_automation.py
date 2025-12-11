# Copyright (c) 2025, Frappe Technologies and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.helpdesk.doctype.hd_ticket.test_hd_ticket import get_ticket_obj
from helpdesk.test_utils import create_base_automation

# On IntegrationTestCase, the doctype test records and all
# link-field test record dependencies are recursively loaded
# Use these module variables to add/remove to/from that list
EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]


class IntegrationTestHDAutomation(IntegrationTestCase):
    """
    Integration tests for HDAutomation.
    Use this class for testing interactions between multiple components.
    """

    def setUp(self):
        # Setup run before every test method.
        create_base_automation()
        pass

    def test_base_automation(self):
        ticket = frappe.get_doc(get_ticket_obj())
        ticket.insert()
        self.assertEqual(ticket.agent_group, "Billing")

        ticket2 = frappe.get_doc(get_ticket_obj())
        ticket2.priority = "High"
        ticket2.insert()
        # ticket2.reload()
        self.assertEqual(ticket2.agent_group, "Product Experts")

    def tearDown(self):
        # Clean up run after every test method.
        pass
