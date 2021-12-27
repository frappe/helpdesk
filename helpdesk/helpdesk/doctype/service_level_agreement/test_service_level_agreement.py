# -*- coding: utf-8 -*-
# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt
from __future__ import unicode_literals

import datetime
import unittest

import frappe
from frappe.utils import flt

from helpdesk.helpdesk.doctype.issue_priority.test_issue_priority import make_priorities


class TestServiceLevelAgreement(unittest.TestCase):
	def setUp(self):
		frappe.db.set_value("Support Settings", None, "track_service_level_agreement", 1)

	def test_service_level_agreement(self):
		# Default Service Level Agreement
		create_default_service_level_agreement = create_service_level_agreement(
			default_service_level_agreement=1,
			holiday_list="__Test Holiday List",
			entity_type=None,
			entity=None,
			response_time=14400,
			resolution_time=21600,
		)

		get_default_service_level_agreement = get_service_level_agreement(
			default_service_level_agreement=1
		)

		self.assertEqual(
			create_default_service_level_agreement.name, get_default_service_level_agreement.name
		)
		self.assertEqual(
			create_default_service_level_agreement.entity_type,
			get_default_service_level_agreement.entity_type,
		)
		self.assertEqual(
			create_default_service_level_agreement.entity,
			get_default_service_level_agreement.entity,
		)
		self.assertEqual(
			create_default_service_level_agreement.default_service_level_agreement,
			get_default_service_level_agreement.default_service_level_agreement,
		)


	def tearDown(self):
		for d in frappe.get_all("Service Level Agreement"):
			frappe.delete_doc("Service Level Agreement", d.name, force=1)


def get_service_level_agreement(
	default_service_level_agreement=None, entity_type=None, entity=None, doctype="Issue"
):
	if default_service_level_agreement:
		filters = {
			"default_service_level_agreement": default_service_level_agreement,
			"document_type": doctype,
		}
	else:
		filters = {"entity_type": entity_type, "entity": entity}

	service_level_agreement = frappe.get_doc("Service Level Agreement", filters)
	return service_level_agreement


def create_service_level_agreement(
	default_service_level_agreement,
	holiday_list,
	response_time,
	entity_type,
	entity,
	resolution_time=0,
	doctype="Issue",
	condition="",
	sla_fulfilled_on=[],
	pause_sla_on=[],
	apply_sla_for_resolution=1,
):

	make_holiday_list()
	make_priorities()

	if not sla_fulfilled_on:
		sla_fulfilled_on = [{"status": "Resolved"}, {"status": "Closed"}]

	pause_sla_on = [{"status": "Replied"}] if doctype == "Issue" else pause_sla_on

	service_level_agreement = frappe._dict(
		{
			"doctype": "Service Level Agreement",
			"enabled": 1,
			"document_type": doctype,
			"service_level": "__Test {} SLA".format(entity_type if entity_type else "Default"),
			"default_service_level_agreement": default_service_level_agreement,
			"condition": condition,
			"default_priority": "Medium",
			"holiday_list": holiday_list,
			"entity_type": entity_type,
			"entity": entity,
			"start_date": frappe.utils.getdate(),
			"end_date": frappe.utils.add_to_date(frappe.utils.getdate(), days=100),
			"apply_sla_for_resolution": apply_sla_for_resolution,
			"priorities": [
				{
					"priority": "Low",
					"response_time": response_time,
					"resolution_time": resolution_time,
				},
				{
					"priority": "Medium",
					"response_time": response_time,
					"default_priority": 1,
					"resolution_time": resolution_time,
				},
				{
					"priority": "High",
					"response_time": response_time,
					"resolution_time": resolution_time,
				},
			],
			"sla_fulfilled_on": sla_fulfilled_on,
			"pause_sla_on": pause_sla_on,
			"support_and_resolution": [
				{"workday": "Monday", "start_time": "10:00:00", "end_time": "18:00:00",},
				{"workday": "Tuesday", "start_time": "10:00:00", "end_time": "18:00:00",},
				{"workday": "Wednesday", "start_time": "10:00:00", "end_time": "18:00:00",},
				{"workday": "Thursday", "start_time": "10:00:00", "end_time": "18:00:00",},
				{"workday": "Friday", "start_time": "10:00:00", "end_time": "18:00:00",},
			],
		}
	)

	filters = {
		"default_service_level_agreement": service_level_agreement.default_service_level_agreement,
		"service_level": service_level_agreement.service_level,
	}

	if not default_service_level_agreement:
		filters.update({"entity_type": entity_type, "entity": entity})

	sla = frappe.db.exists("Service Level Agreement", filters)
	if sla:
		frappe.delete_doc("Service Level Agreement", sla, force=1)

	return frappe.get_doc(service_level_agreement).insert(ignore_permissions=True)


def make_holiday_list():
	holiday_list = frappe.db.exists("Holiday List", "__Test Holiday List")
	if not holiday_list:
		holiday_list = frappe.get_doc(
			{
				"doctype": "Holiday List",
				"holiday_list_name": "__Test Holiday List",
				"from_date": "2019-01-01",
				"to_date": "2019-12-31",
				"holidays": [
					{"description": "Test Holiday 1", "holiday_date": "2019-03-05"},
					{"description": "Test Holiday 2", "holiday_date": "2019-03-07"},
					{"description": "Test Holiday 3", "holiday_date": "2019-02-11"},
				],
			}
		).insert()