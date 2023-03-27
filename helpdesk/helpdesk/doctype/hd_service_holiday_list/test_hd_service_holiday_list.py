# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import unittest
from datetime import timedelta

import frappe
from frappe.utils import getdate


class TestHDServiceHolidayList(unittest.TestCase):
	def test_hd_service_holiday_list(self):
		today_date = getdate()
		test_holiday_dates = [today_date - timedelta(days=5), today_date - timedelta(days=4)]
		hd_service_holiday_list = make_hd_service_holiday_list(
			"test_hd_service_holiday_list",
			holiday_dates=[
				{"holiday_date": test_holiday_dates[0], "description": "test holiday"},
				{"holiday_date": test_holiday_dates[1], "description": "test holiday2"},
			],
		)
		fetched_hd_service_holiday_list = frappe.get_value(
			"HD Service Holiday List", hd_service_holiday_list.name
		)
		self.assertEqual(hd_service_holiday_list.name, fetched_hd_service_holiday_list)


def make_hd_service_holiday_list(
	name, from_date=getdate() - timedelta(days=10), to_date=getdate(), holiday_dates=None
):
	frappe.delete_doc_if_exists("HD Service Holiday List", name, force=1)
	doc = frappe.get_doc(
		{
			"doctype": "HD Service Holiday List",
			"holiday_list_name": name,
			"from_date": from_date,
			"to_date": to_date,
			"holidays": holiday_dates,
		}
	).insert()
	return doc
