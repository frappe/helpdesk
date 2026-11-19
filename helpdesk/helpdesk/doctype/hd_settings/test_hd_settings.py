# -*- coding: utf-8 -*-
# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt
import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import set_request
from frappe.website.serve import get_response
from frappe.website.utils import get_home_page

from helpdesk.helpdesk.doctype.hd_settings.helpers import (
    KNOWLEDGE_BASE_HOME,
    TICKETS_HOME,
)
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
        # get_response commits, so the rollback alone would leave the setting off.
        prefer = frappe.db.get_single_value("HD Settings", "prefer_knowledge_base")
        self.addCleanup(self.restore_prefer_knowledge_base, prefer)
        frappe.db.set_single_value("HD Settings", "prefer_knowledge_base", 0)

    def tearDown(self) -> None:
        frappe.set_user("Administrator")

    def restore_prefer_knowledge_base(self, value) -> None:
        frappe.db.set_single_value("HD Settings", "prefer_knowledge_base", value)
        frappe.db.commit()  # nosemgrep

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

    def setUp(self) -> None:
        frappe.db.set_single_value("HD Settings", {"brand_logo": "", "favicon": ""})
        frappe.db.set_single_value("Website Settings", "app_logo", "")

    def test_the_logo_marks_auth_emails(self) -> None:
        self.assertEqual(
            self.set_brand("/files/logo.png", "/files/icon.png"), "/files/logo.png"
        )

    def test_an_icon_only_brand_marks_auth_emails(self) -> None:
        self.assertEqual(self.set_brand(favicon="/files/icon.png"), "/files/icon.png")

    def test_removing_the_brand_image_clears_it(self) -> None:
        self.set_brand(favicon="/files/icon.png")
        self.assertFalse(self.set_brand())

    def test_a_logo_set_elsewhere_stays(self) -> None:
        frappe.db.set_single_value("Website Settings", "app_logo", "/files/theirs.png")
        self.assertEqual(self.set_brand("/files/logo.png"), "/files/theirs.png")
        self.assertEqual(self.set_brand(), "/files/theirs.png")


class TestKnowledgeBaseHomePage(IntegrationTestCase):
    """The setting makes the knowledge base the site's home page for guests."""

    def set_setting(self, value: int) -> str:
        settings = frappe.get_single("HD Settings")
        settings.knowledge_base_home_page_for_guests = value
        settings.save()
        return frappe.db.get_single_value("Website Settings", "home_page")

    def guest_home_page(self) -> str:
        frappe.set_user("Guest")
        try:
            return get_home_page()
        finally:
            frappe.set_user("Administrator")

    def setUp(self) -> None:
        frappe.db.set_single_value("Website Settings", "home_page", "")
        frappe.db.set_single_value(
            "HD Settings", "knowledge_base_home_page_for_guests", 0
        )
        frappe.db.set_single_value("HD Settings", "public_knowledge_base", 1)
        frappe.clear_cache()

    def test_guests_land_on_the_knowledge_base(self) -> None:
        self.assertEqual(self.set_setting(1), "help")
        self.assertEqual(self.guest_home_page(), "help")

    def test_turning_it_off_restores_the_login_page(self) -> None:
        self.set_setting(1)
        self.assertFalse(self.set_setting(0))
        self.assertEqual(self.guest_home_page(), "login")

    def test_turning_it_off_keeps_a_home_page_set_elsewhere(self) -> None:
        self.set_setting(1)
        frappe.db.set_single_value("Website Settings", "home_page", "about")
        self.assertEqual(self.set_setting(0), "about")

    def test_making_the_knowledge_base_private_turns_it_off(self) -> None:
        self.set_setting(1)
        settings = frappe.get_single("HD Settings")
        settings.public_knowledge_base = 0
        settings.save()
        self.assertEqual(settings.knowledge_base_home_page_for_guests, 0)
        self.assertEqual(self.guest_home_page(), "login")


class TestGuestOnlySettings(IntegrationTestCase):
    """Guests reach only a public knowledge base, so their settings need one."""

    GUEST_ONLY = (
        "allow_anonymous_article_voting",
        "knowledge_base_home_page_for_guests",
    )

    def setUp(self) -> None:
        frappe.db.set_single_value(
            "HD Settings",
            {field: 0 for field in self.GUEST_ONLY} | {"public_knowledge_base": 0},
        )

    def turn_on(self, field: str):
        settings = frappe.get_single("HD Settings")
        settings.set(field, 1)
        return settings.save()

    def test_cannot_turn_on_while_private(self) -> None:
        for field in self.GUEST_ONLY:
            with self.subTest(field=field), self.assertRaises(frappe.ValidationError):
                self.turn_on(field)

    def test_can_turn_on_while_public(self) -> None:
        frappe.db.set_single_value("HD Settings", "public_knowledge_base", 1)
        for field in self.GUEST_ONLY:
            self.assertEqual(self.turn_on(field).get(field), 1)

    def test_a_site_already_in_that_state_still_saves(self) -> None:
        frappe.db.set_single_value("HD Settings", "allow_anonymous_article_voting", 1)
        settings = frappe.get_single("HD Settings")
        before = settings.prefer_knowledge_base
        self.addCleanup(
            frappe.db.set_single_value, "HD Settings", "prefer_knowledge_base", before
        )
        settings.prefer_knowledge_base = int(not before)
        settings.save()


class TestBannerImage(IntegrationTestCase):
    def save_banner(self, url: str):
        settings = frappe.get_single("HD Settings")
        settings.banner_image = url
        return settings.save()

    def tearDown(self) -> None:
        frappe.db.set_single_value("HD Settings", "banner_image", None)

    def test_a_linked_image_is_refused(self) -> None:
        with self.assertRaises(frappe.ValidationError):
            self.save_banner("https://tracker.example.com/pixel.png")

    def test_an_uploaded_image_saves(self) -> None:
        self.assertEqual(
            self.save_banner("/files/banner.png").banner_image, "/files/banner.png"
        )


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
