# -*- coding: utf-8 -*-
# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt
import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.test_utils import SLA_PRIORITY_NAME, make_sla, make_ticket


class TestHDServiceLevelAgreement(IntegrationTestCase):
    def setUp(self):
        pass

    def test_sla_creation(self):
        sla = make_sla("Test SLA")
        self.assertTrue(sla.name, "Test SLA")

    def test_sla_assignment(self):
        ticket = make_ticket(priority="High")
        sla = frappe.get_doc("HD Service Level Agreement", SLA_PRIORITY_NAME)
        self.assertEqual(ticket.sla, sla.name)
        self.assertEqual(ticket.priority, "High")

    def test_default_sla_assignment(self):
        ticket = make_ticket(priority="Low")
        self.assertEqual(ticket.sla, SLA_PRIORITY_NAME)
