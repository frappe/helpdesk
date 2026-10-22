# -*- coding: utf-8 -*-
# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt
import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import set_request
from frappe.website.serve import get_response

from helpdesk.helpdesk.doctype.hd_settings.helpers import (
    KNOWLEDGE_BASE_HOME,
    TICKETS_HOME,
)
from helpdesk.setup.install import setup_customer_role
from helpdesk.test_utils import create_agent

CUSTOMER = "home-page-customer@example.com"
AGENT_CUSTOMER = "home-page-agent@example.com"


class TestCustomerHomePage(IntegrationTestCase):
    def open_desk(self, user: str, path: str = "/helpdesk"):
        frappe.set_user(user)
        set_request(method="GET", path=path)
        return get_response()

    def setUp(self) -> None:
        make_customer(CUSTOMER)
        create_agent(AGENT_CUSTOMER)
        frappe.get_doc("User", AGENT_CUSTOMER).add_roles("HD Customer")
        frappe.db.set_single_value("HD Settings", "prefer_knowledge_base", 0)

    def tearDown(self) -> None:
        frappe.set_user("Administrator")

    def test_customer_roles_keep_the_desk_as_home(self) -> None:
        setup_customer_role(fresh_install=False)
        self.assertEqual(
            frappe.db.get_value("Role", "HD Customer", "home_page"), "/helpdesk"
        )

    def test_customers_go_on_to_their_tickets(self) -> None:
        response = self.open_desk(CUSTOMER)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], TICKETS_HOME)

    def test_customers_go_on_to_the_knowledge_base_when_preferred(self) -> None:
        frappe.db.set_single_value("HD Settings", "prefer_knowledge_base", 1)
        self.assertEqual(
            self.open_desk(CUSTOMER).headers["Location"], KNOWLEDGE_BASE_HOME
        )

    def test_an_agent_who_is_also_a_customer_stays_on_the_desk(self) -> None:
        self.assertEqual(self.open_desk(AGENT_CUSTOMER).status_code, 200)

    def test_a_deep_link_is_left_to_the_desk_router(self) -> None:
        response = self.open_desk(CUSTOMER, "/helpdesk/tickets/1")
        self.assertEqual(response.status_code, 200)


class TestEmailBrandImage(IntegrationTestCase):
    """Sign-in and invite emails show Website Settings' app logo."""

    def set_brand(self, brand_logo: str = "", favicon: str = "") -> str:
        settings = frappe.get_single("HD Settings")
        settings.update({"brand_logo": brand_logo, "favicon": favicon})
        settings.save()
        return frappe.db.get_single_value("Website Settings", "app_logo")

    def test_the_logo_marks_auth_emails(self) -> None:
        self.assertEqual(
            self.set_brand("/files/logo.png", "/files/icon.png"), "/files/logo.png"
        )

    def test_an_icon_only_brand_marks_auth_emails(self) -> None:
        self.assertEqual(self.set_brand(favicon="/files/icon.png"), "/files/icon.png")

    def test_removing_the_brand_image_clears_it(self) -> None:
        self.set_brand(favicon="/files/icon.png")
        self.assertFalse(self.set_brand())


def make_customer(email: str) -> None:
    if frappe.db.exists("User", email):
        return
    user = frappe.get_doc(
        {
            "doctype": "User",
            "email": email,
            "first_name": "Home Page",
            "send_welcome_email": 0,
            "user_type": "Website User",
        }
    ).insert(ignore_permissions=True)
    user.add_roles("HD Customer")
