# -*- coding: utf-8 -*-
# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt
import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.helpdesk.doctype.hd_settings.helpers import (
    KNOWLEDGE_BASE_HOME,
    TICKETS_HOME,
)


class TestCustomerHomePage(IntegrationTestCase):
    """`prefer_knowledge_base` decides where customers land: the roles and the portal default follow it."""

    def set_prefer_knowledge_base(self, value: int) -> None:
        settings = frappe.get_single("HD Settings")
        settings.prefer_knowledge_base = value
        settings.save(ignore_permissions=True)

    def home_pages(self) -> set[str]:
        roles = frappe.get_all(
            "Role",
            filters={"name": ["in", ["HD Customer", "HD Customer Manager"]]},
            pluck="home_page",
        )
        portal = frappe.db.get_single_value("Portal Settings", "default_portal_home")
        return {*roles, portal}

    def setUp(self) -> None:
        frappe.db.set_value(
            "Role",
            {"name": ["in", ["HD Customer", "HD Customer Manager"]]},
            "home_page",
            TICKETS_HOME,
        )
        frappe.db.set_single_value(
            "Portal Settings", "default_portal_home", TICKETS_HOME
        )
        frappe.db.set_single_value("HD Settings", "prefer_knowledge_base", 0)

    def test_turning_it_on_sends_customers_to_the_knowledge_base(self) -> None:
        self.set_prefer_knowledge_base(1)
        self.assertEqual(self.home_pages(), {KNOWLEDGE_BASE_HOME})

    def test_turning_it_off_sends_customers_to_their_tickets(self) -> None:
        self.set_prefer_knowledge_base(1)
        self.set_prefer_knowledge_base(0)
        self.assertEqual(self.home_pages(), {TICKETS_HOME})

    def test_a_home_page_set_by_hand_is_kept(self) -> None:
        frappe.db.set_value("Role", "HD Customer", "home_page", "/custom")
        self.set_prefer_knowledge_base(1)
        self.assertEqual(
            frappe.db.get_value("Role", "HD Customer", "home_page"), "/custom"
        )
