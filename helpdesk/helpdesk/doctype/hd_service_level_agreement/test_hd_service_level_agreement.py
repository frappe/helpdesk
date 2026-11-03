# -*- coding: utf-8 -*-
# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt
from datetime import timedelta

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_to_date, get_datetime, getdate

from helpdesk.consts import DEFAULT_SLA
from helpdesk.test_utils import (
    SLA_PRIORITY_NAME,
    add_holiday,
    get_current_week_monday,
    make_priority,
    make_sla,
    make_ticket,
    remove_holidays,
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

    def at(self, day: int, hours: float):
        """A moment in the current week, day 0 being Monday."""
        monday = get_datetime(get_current_week_monday(hours=0))
        return monday + timedelta(days=day, hours=hours)

    def with_breaks(self, sla, break_start="13:00:00", break_end="14:00:00"):
        """Give every workday of `sla` the same break, in memory only."""
        for row in sla.support_and_resolution:
            row.break_start, row.break_end = break_start, break_end
        return sla

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

    def test_break_validation(self):
        """A break needs both ends and must sit strictly inside the workday."""
        sla = frappe.get_doc(DOCTYPE, SLA_PRIORITY_NAME)
        sla.validate_support_and_resolution()  # no break is still valid

        invalid = [
            ("13:00:00", None),
            (None, "14:00:00"),
            ("10:00:00", "11:00:00"),  # starts with the workday
            ("09:00:00", "11:00:00"),  # starts before the workday
            ("17:00:00", "18:00:00"),  # ends with the workday
            ("14:00:00", "14:00:00"),
            ("14:00:00", "13:00:00"),
        ]
        for break_start, break_end in invalid:
            with self.subTest(break_start=break_start, break_end=break_end):
                self.with_breaks(sla, break_start, break_end)
                with self.assertRaisesRegex(frappe.ValidationError, "row <u>1</u>"):
                    sla.validate_support_and_resolution()

        self.with_breaks(sla, "10:00:01", "17:59:59")
        sla.validate_support_and_resolution()

    def test_targets_skip_break(self):
        """High is 1h to respond and 4h to resolve, Mon-Fri 10:00-18:00."""
        plain = frappe.get_doc(DOCTYPE, SLA_PRIORITY_NAME)
        breaking = self.with_breaks(frappe.get_doc(DOCTYPE, SLA_PRIORITY_NAME))
        cases = [
            # start, target, hold, without break, with 13:00-14:00 break
            (self.at(0, 12 + 50 / 60), "response_time", 0, 13 + 50 / 60, 14 + 50 / 60),
            (self.at(0, 12), "response_time", 0, 13, 13),  # ends at break start
            (self.at(0, 13 + 20 / 60), "response_time", 0, 14 + 20 / 60, 15),
            (
                self.at(0, 12 + 50 / 60),
                "resolution_time",
                0,
                16 + 50 / 60,
                17 + 50 / 60,
            ),
            (self.at(0, 12), "resolution_time", 3600, 17, 18),  # hold time
            # 30m on Monday, the rest on Tuesday around its break
            (self.at(0, 17.5), "resolution_time", 0, 24 + 13.5, 24 + 14.5),
        ]
        for start, target, hold, without_break, with_break in cases:
            with self.subTest(start=start, target=target):
                for sla, hours in ((plain, without_break), (breaking, with_break)):
                    self.assertEqual(
                        sla.calc_time(start, "High", target, hold_time=hold),
                        self.at(0, hours),
                    )

    def test_elapsed_time_skips_break(self):
        plain = frappe.get_doc(DOCTYPE, SLA_PRIORITY_NAME)
        breaking = self.with_breaks(frappe.get_doc(DOCTYPE, SLA_PRIORITY_NAME))
        hour = 3600
        cases = [
            # start, end, without break, with 13:00-14:00 break
            (self.at(0, 12.5), self.at(0, 14.5), 2 * hour, hour),  # across
            (self.at(0, 12.5), self.at(0, 13.5), hour, hour / 2),  # into
            (self.at(0, 13.5), self.at(0, 14.5), hour, hour / 2),  # out of
            (self.at(0, 13.1), self.at(0, 13.9), 0.8 * hour, 0),  # inside
            (self.at(0, 14.5), self.at(0, 12.5), 0, 0),  # backwards
        ]
        for start, end, without_break, with_break in cases:
            with self.subTest(start=start, end=end):
                self.assertAlmostEqual(
                    plain.calc_elapsed_time(start, end), without_break
                )
                self.assertAlmostEqual(
                    breaking.calc_elapsed_time(start, end), with_break
                )

        # Monday from noon, Tuesday off, Wednesday in full, Thursday until 11:00
        add_holiday(getdate(self.at(1, 0)), "Break test holiday")
        self.addCleanup(remove_holidays)
        start, end = self.at(0, 12), self.at(3, 11)
        self.assertEqual(plain.calc_elapsed_time(start, end), (6 + 8 + 1) * hour)
        self.assertEqual(breaking.calc_elapsed_time(start, end), (5 + 7 + 1) * hour)

    def test_ticket_picks_up_break_on_next_update(self):
        """Saving a break moves targets of tickets only once they are updated,
        and a ticket raised during the break is outside working hours."""
        with self.freeze_time(self.at(0, 12 + 50 / 60)):
            ticket = make_ticket(priority="High")
        self.assertEqual(get_datetime(ticket.response_by), self.at(0, 13 + 50 / 60))

        sla = self.with_breaks(frappe.get_doc(DOCTYPE, SLA_PRIORITY_NAME))
        sla.save()
        self.addCleanup(lambda: self.with_breaks(sla.reload(), None, None).save())

        ticket.reload()
        self.assertEqual(get_datetime(ticket.response_by), self.at(0, 13 + 50 / 60))
        with self.freeze_time(self.at(0, 12 + 55 / 60)):
            ticket.save()
        self.assertEqual(get_datetime(ticket.response_by), self.at(0, 14 + 50 / 60))

        with self.freeze_time(self.at(0, 13.5)):
            during_break = make_ticket(priority="High")
            self.assertTrue(during_break.raised_outside_working_hours)
            self.assertTrue(during_break.is_currently_outside_working_hours())
        with self.freeze_time(self.at(0, 14.5)):
            self.assertFalse(during_break.is_currently_outside_working_hours())
        # the banner holds until the next day starts, not until the break ends
        self.assertEqual(
            sla.get_next_working_day_start(self.at(0, 13.5)), self.at(1, 10)
        )
