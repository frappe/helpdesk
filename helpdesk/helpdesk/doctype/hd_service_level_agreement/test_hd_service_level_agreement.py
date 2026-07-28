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

    def test_blank_condition_sla_is_not_a_false_positive(self):
        # An enabled, non-default SLA with a blank ("" or NULL) condition
        # must not match tickets; only the default SLA is a catch-all
        empty = make_sla("Empty Condition SLA")
        null = make_sla("Null Condition SLA")
        frappe.db.set_value("HD Service Level Agreement", null.name, "condition", None)
        for sla in (empty, null):
            self.addCleanup(
                frappe.db.set_value,
                "HD Service Level Agreement",
                sla.name,
                "enabled",
                0,
            )

        # Medium matches no conditional SLA, so the default SLA must win
        ticket = make_ticket(priority="Medium")
        self.assertEqual(ticket.sla, "Default")

    def test_demoted_default_sla_is_not_catch_all(self):
        # Promoting another SLA as default demotes the seeded "Default" SLA,
        # which stays enabled with a blank condition. It must not keep
        # matching every ticket ahead of the new default.
        new_default = make_sla("New Default SLA").reload()
        new_default.default_sla = 1
        new_default.save()

        def restore():
            default = frappe.get_doc("HD Service Level Agreement", "Default")
            default.default_sla = 1
            default.save()
            frappe.db.set_value(
                "HD Service Level Agreement", new_default.name, "enabled", 0
            )

        self.addCleanup(restore)

        # premise: saving the new default actually demoted "Default"
        self.assertEqual(
            frappe.db.get_value("HD Service Level Agreement", "Default", "default_sla"),
            0,
        )

        # Medium matches no conditional SLA, so the new default must win
        ticket = make_ticket(priority="Medium")
        self.assertEqual(ticket.sla, new_default.name)
