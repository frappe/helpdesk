# -*- coding: utf-8 -*-
# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt
import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_to_date, get_datetime

from helpdesk.consts import DEFAULT_SLA
from helpdesk.test_utils import (
    SLA_PRIORITY_NAME,
    get_current_week_monday,
    make_priority,
    make_sla,
    make_ticket,
)

DOCTYPE = "HD Service Level Agreement"
UNINCLUDED_PRIORITY = "Critical"  # deliberately absent from every seeded SLA


class TestHDServiceLevelAgreement(IntegrationTestCase):
    def setUp(self):
        pass

    def drop_priority(self, sla, priority: str):
        """Remove a priority row from a policy that already has tickets on it."""
        sla.reload()
        sla.priorities = [row for row in sla.priorities if row.priority != priority]
        sla.save()

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
        # must not match tickets; only the Default SLA matches everything
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
        self.assertEqual(ticket.sla, DEFAULT_SLA)

    def test_demoted_default_sla_stops_matching_everything(self):
        # Promoting another SLA as default demotes the seeded SLA,
        # which stays enabled with a blank condition. It must not keep
        # matching every ticket ahead of the new Default SLA.
        new_default = make_sla("New Default SLA").reload()
        new_default.default_sla = 1
        new_default.save()

        def restore():
            default = frappe.get_doc("HD Service Level Agreement", DEFAULT_SLA)
            default.default_sla = 1
            default.save()
            frappe.db.set_value(
                "HD Service Level Agreement", new_default.name, "enabled", 0
            )

        self.addCleanup(restore)

        # premise: saving the new default actually demoted the seeded SLA
        self.assertEqual(
            frappe.db.get_value(
                "HD Service Level Agreement", DEFAULT_SLA, "default_sla"
            ),
            0,
        )

        # Medium matches no conditional SLA, so the new default must win
        ticket = make_ticket(priority="Medium")
        self.assertEqual(ticket.sla, new_default.name)

    def test_default_sla_is_optional(self):
        """A site may run with no Default SLA: it can be unticked and deleted."""

        def restore():
            default = frappe.get_doc(DOCTYPE, DEFAULT_SLA)
            default.default_sla = 1
            default.save()

        self.addCleanup(restore)

        default = frappe.get_doc(DOCTYPE, DEFAULT_SLA)
        default.default_sla = 0
        default.save()
        self.assertFalse(frappe.db.get_value(DOCTYPE, DEFAULT_SLA, "default_sla"))

        # a conditional policy still saves with no Default SLA on the site
        conditional = make_sla("No Default SLA", "doc.priority == 'Medium'")
        self.addCleanup(frappe.db.set_value, DOCTYPE, conditional.name, "enabled", 0)

        # and the last remaining default can be deleted outright
        conditional.reload()
        conditional.default_sla = 1
        conditional.save()
        frappe.delete_doc(DOCTYPE, conditional.name)
        self.assertFalse(frappe.db.exists(DOCTYPE, {"default_sla": 1}))

    def test_priority_removed_from_sla_detaches_ticket(self):
        """Dropping a priority a ticket uses takes that ticket out of the policy."""
        # a priority no other policy includes, so the ticket cannot swap away
        make_priority(UNINCLUDED_PRIORITY)
        raised_at = get_current_week_monday(hours=12)
        sla = make_sla(
            "Droppable SLA",
            f"doc.priority == '{UNINCLUDED_PRIORITY}'",
            priorities=["Low", UNINCLUDED_PRIORITY],
        )
        self.addCleanup(frappe.db.set_value, DOCTYPE, sla.name, "enabled", 0)

        with self.freeze_time(raised_at):
            ticket = make_ticket(priority=UNINCLUDED_PRIORITY)
        self.assertEqual(ticket.sla, sla.name)

        self.drop_priority(sla, UNINCLUDED_PRIORITY)

        with self.freeze_time(add_to_date(raised_at, hours=1)):
            ticket.reload()
            ticket.save()

        self.assertFalse(ticket.sla)
        self.assertFalse(ticket.response_by)
        # the clock start survives, so a later re-attach resumes it
        self.assertEqual(
            get_datetime(ticket.service_level_agreement_creation), raised_at
        )

    def test_warns_when_default_sla_untick_affects_tickets(self):
        """Unticking the Default SLA warns: every ticket on it detaches on its next save."""

        def restore_default():
            default = frappe.get_doc(DOCTYPE, DEFAULT_SLA)
            default.default_sla = 1
            default.save()

        self.addCleanup(restore_default)

        # a Default SLA with nothing on it says nothing
        empty = make_sla("Empty Default SLA").reload()
        self.addCleanup(frappe.db.set_value, DOCTYPE, empty.name, "enabled", 0)
        empty.default_sla = 1
        empty.save()

        frappe.clear_messages()
        empty.reload()
        empty.default_sla = 0
        empty.save()
        self.assertFalse(frappe.get_message_log())

        restore_default()
        ticket = make_ticket(priority="Medium")  # only the Default SLA matches Medium
        self.assertEqual(ticket.sla, DEFAULT_SLA)

        frappe.clear_messages()
        default = frappe.get_doc(DOCTYPE, DEFAULT_SLA)
        default.default_sla = 0
        default.save()
        self.assertIn("lose", frappe.as_json(frappe.get_message_log()))

    def test_warns_when_disabling_sla_with_open_tickets(self):
        """Disabling a policy warns: every ticket on it detaches on its next save."""
        sla = make_sla("Disablable SLA", "doc.priority == 'Medium'")
        self.addCleanup(frappe.db.set_value, DOCTYPE, sla.name, "enabled", 0)

        # an enabled policy with nothing on it says nothing
        frappe.clear_messages()
        sla.reload()
        sla.enabled = 0
        sla.save()
        self.assertFalse(frappe.get_message_log())

        sla.reload()
        sla.enabled = 1
        sla.save()
        ticket = make_ticket(priority="Medium")
        self.assertEqual(ticket.sla, sla.name)

        frappe.clear_messages()
        sla.reload()
        sla.enabled = 0
        sla.save()
        self.assertIn("lose", frappe.as_json(frappe.get_message_log()))

    def test_warns_when_removing_priority_used_by_open_tickets(self):
        """Removing a priority warns only when open tickets actually use it."""
        unused = make_sla(
            "Unused Priority SLA", "doc.priority == 'High'", priorities=["Low", "High"]
        )
        self.addCleanup(frappe.db.set_value, DOCTYPE, unused.name, "enabled", 0)

        frappe.clear_messages()
        self.drop_priority(unused, "High")
        self.assertFalse(frappe.get_message_log())

        used = make_sla(
            "Used Priority SLA",
            "doc.priority == 'Medium'",
            priorities=["Low", "Medium"],
        )
        self.addCleanup(frappe.db.set_value, DOCTYPE, used.name, "enabled", 0)
        ticket = make_ticket(priority="Medium")
        self.assertEqual(ticket.sla, used.name)

        frappe.clear_messages()
        self.drop_priority(used, "Medium")
        self.assertIn("Medium", frappe.as_json(frappe.get_message_log()))
