# -*- coding: utf-8 -*-
# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt
from __future__ import unicode_literals

import unittest
from datetime import datetime

import frappe


class TestHDSettingsWorkingHours(unittest.TestCase):
    """
    Testing for outside working hours notification functionality
    """

    def setup_standard_work_week(self):
        self.settings = frappe.get_doc("HD Settings")
        self.settings.update(
            {
                "show_message_outside_working_hours": 1,
                "outside_hours_message": "We are currently closed. We will get back to you during business hours.",
                "monday": 1,
                "tuesday": 1,
                "wednesday": 1,
                "thursday": 1,
                "friday": 1,
                "saturday": 0,
                "sunday": 0,
                "work_start_time": "09:00:00",
                "work_end_time": "17:00:00",
            }
        )
        self.settings.save()

    def run_check_working_hours_at(self, mock_time: datetime):
        """
        Mocks the time and calls the check_working_hours API.
        """
        patch_target = "helpdesk.helpdesk.doctype.hd_settings.hd_settings.now_datetime"

        with unittest.mock.patch(patch_target, return_value=mock_time):
            response = frappe.call(
                "helpdesk.helpdesk.doctype.hd_settings.hd_settings.check_working_hours"
            )
            return response

    def test_feature_disabled(self):
        """
        Test that no message is shown if the feature is disabled, even if it's outside working hours.
        """
        self.setup_standard_work_week()
        self.settings.show_message_outside_working_hours = 0
        self.settings.save()

        mock_time = datetime(2025, 10, 19, 12, 0, 0)

        response = self.run_check_working_hours_at(mock_time)

        self.assertFalse(response.get("show_message"))

    def test_outside_working_day(self):
        """
        Test that the message is shown on a non-working day (e.g., Sunday).
        """
        self.setup_standard_work_week()
        mock_time = datetime(2025, 10, 19, 14, 0, 0)

        response = self.run_check_working_hours_at(mock_time)

        self.assertTrue(response.get("show_message"))
        self.assertEqual(response.get("message"), self.settings.outside_hours_message)

    def test_inside_working_day_before_hours(self):
        """
        Test that the message is shown on a working day but before work starts.
        """
        self.setup_standard_work_week()
        mock_time = datetime(2025, 10, 20, 8, 0, 0)

        response = self.run_check_working_hours_at(mock_time)

        self.assertTrue(response.get("show_message"))
        self.assertEqual(response.get("message"), self.settings.outside_hours_message)

    def test_inside_working_day_after_hours(self):
        """
        Test that the message is shown on a working day but after work ends.
        """
        self.setup_standard_work_week()
        mock_time = datetime(2025, 10, 20, 18, 0, 0)

        response = self.run_check_working_hours_at(mock_time)

        self.assertTrue(response.get("show_message"))

    def test_inside_working_hours(self):
        """
        Test that no message is shown when raising a ticket during working days and hours.
        """
        self.setup_standard_work_week()
        mock_time = datetime(2025, 10, 20, 12, 0, 0)

        response = self.run_check_working_hours_at(mock_time)

        self.assertFalse(response.get("show_message"))

    def test_working_day_with_no_times_set(self):
        """
        Test edge case: If a day is a working day but no start/end times
        are set, it should be considered "always on" for that day.
        """
        self.setup_standard_work_week()
        self.settings.work_start_time = None
        self.settings.work_end_time = None
        self.settings.save()

        mock_time = datetime(2025, 10, 20, 2, 0, 0)

        response = self.run_check_working_hours_at(mock_time)

        self.assertFalse(response.get("show_message"))

    def test_empty_message(self):
        """
        Test that the message is an empty string if it's not set in settings.
        """
        self.setup_standard_work_week()
        self.settings.outside_hours_message = ""
        self.settings.save()

        mock_time = datetime(2025, 10, 19, 14, 0, 0)

        response = self.run_check_working_hours_at(mock_time)

        self.assertTrue(response.get("show_message"))
        self.assertEqual(response.get("message"), "")
