from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.helpdesk.hooks.portal import (
    get_website_user_home_page,
    grant_customer_role,
    grant_customer_role_on_signup,
    is_helpdesk_path,
)
from helpdesk.patches import revert_portal_defaults
from helpdesk.test_utils import create_agent, get_user_roles, make_user, unique_email
from helpdesk.utils import AGENT_PORTAL_ROOT, CUSTOMER_PORTAL_ROOT

HOOKS = "helpdesk.helpdesk.hooks.portal"


class TestHomePage(IntegrationTestCase):
    def home_page(self, user: str, helpdesk_only: bool) -> str | None:
        with (
            self.set_user(user),
            patch(f"{HOOKS}.is_helpdesk_only_app", return_value=helpdesk_only),
        ):
            return get_website_user_home_page(user)

    def test_guest_gets_no_home_page(self) -> None:
        self.assertIsNone(self.home_page("Guest", helpdesk_only=True))

    def test_customer_lands_on_the_portal(self) -> None:
        customer = make_user("home_customer", "HD Customer")
        for helpdesk_only in (True, False):
            self.assertEqual(
                self.home_page(customer, helpdesk_only), CUSTOMER_PORTAL_ROOT
            )

    def test_website_user_of_another_app_keeps_its_home(self) -> None:
        user = make_user("home_other_app")
        self.assertIsNone(self.home_page(user, helpdesk_only=False))
        self.assertEqual(self.home_page(user, helpdesk_only=True), CUSTOMER_PORTAL_ROOT)

    def test_agent_lands_on_the_desk_when_helpdesk_is_the_only_app(self) -> None:
        agent = create_agent(unique_email("home_agent")).name
        self.assertEqual(self.home_page(agent, helpdesk_only=True), AGENT_PORTAL_ROOT)
        self.assertIsNone(self.home_page(agent, helpdesk_only=False))

    def test_agent_lands_on_the_desk_when_helpdesk_is_their_default_app(self) -> None:
        agent = create_agent(unique_email("home_default_app")).name
        frappe.db.set_value("User", agent, "default_app", "helpdesk")
        self.assertEqual(self.home_page(agent, helpdesk_only=False), AGENT_PORTAL_ROOT)

    def test_system_manager_lands_on_the_desk_when_helpdesk_is_the_only_app(
        self,
    ) -> None:
        manager = make_user("home_manager", "System Manager")
        self.assertEqual(self.home_page(manager, helpdesk_only=True), AGENT_PORTAL_ROOT)

    def test_desk_user_without_helpdesk_roles_keeps_its_home(self) -> None:
        user = make_user("home_desk_user", "Website Manager", "HD Customer")
        for helpdesk_only in (True, False):
            self.assertIsNone(self.home_page(user, helpdesk_only))


class TestSignupGrant(IntegrationTestCase):
    def sign_up(self, redirect_to: str | None, user_type: str = "Website User"):
        user_doc = frappe.new_doc(
            "User", email=unique_email("signup"), user_type=user_type
        )
        with patch.dict(frappe.local.form_dict, {"redirect_to": redirect_to}):
            grant_customer_role_on_signup(user_doc)
        return [row.role for row in user_doc.roles]

    def test_signup_from_helpdesk_gets_the_customer_role(self) -> None:
        for redirect_to in (AGENT_PORTAL_ROOT, f"{CUSTOMER_PORTAL_ROOT}/tickets"):
            self.assertEqual(self.sign_up(redirect_to), ["HD Customer"], redirect_to)

    def test_signup_from_elsewhere_gets_no_role(self) -> None:
        for redirect_to in (None, "/login", "/app", f"{AGENT_PORTAL_ROOT}x"):
            self.assertEqual(self.sign_up(redirect_to), [], redirect_to)

    def test_system_user_gets_no_role(self) -> None:
        self.assertEqual(
            self.sign_up(CUSTOMER_PORTAL_ROOT, user_type="System User"), []
        )

    def test_helpdesk_path_ignores_query_and_full_urls(self) -> None:
        self.assertTrue(is_helpdesk_path(f"{AGENT_PORTAL_ROOT}?q=1"))
        self.assertTrue(
            is_helpdesk_path(f"https://example.com{CUSTOMER_PORTAL_ROOT}/kb")
        )


class TestVisitGrant(IntegrationTestCase):
    def setUp(self) -> None:
        self.addCleanup(setattr, frappe.local.flags, "commit", False)

    def test_first_visit_grants_the_customer_role_once(self) -> None:
        user = make_user("visit_customer")
        grant_customer_role(user)
        grant_customer_role(user)
        self.assertEqual(get_user_roles(user).count("HD Customer"), 1)
        self.assertTrue(frappe.local.flags.commit)

    def test_system_user_and_guest_get_no_role(self) -> None:
        manager = make_user("visit_manager", "System Manager")
        grant_customer_role(manager)
        grant_customer_role("Guest")
        self.assertNotIn("HD Customer", get_user_roles(manager))
        self.assertNotIn("HD Customer", get_user_roles("Guest"))

    def test_a_failed_save_keeps_the_portal_up(self) -> None:
        user = make_user("visit_failure")
        with (
            patch(
                "frappe.core.doctype.user.user.User.add_roles", side_effect=Exception
            ),
            patch.object(frappe.db, "rollback") as rollback,
            patch("frappe.log_error") as log_error,
        ):
            grant_customer_role(user)
        rollback.assert_called_once()
        log_error.assert_called_once()
        self.assertFalse(frappe.local.flags.commit)


class TestRevertPortalDefaults(IntegrationTestCase):
    def set_portal_settings(self, home: str | None, role: str | None) -> None:
        frappe.db.set_single_value(
            "Portal Settings", {"default_portal_home": home, "default_role": role}
        )

    def run_patch(self):
        with patch.object(revert_portal_defaults, "notify_system_managers") as notify:
            revert_portal_defaults.execute()
        return notify

    def test_clears_what_helpdesk_wrote(self) -> None:
        self.set_portal_settings("/helpdesk", "HD Customer")
        frappe.db.set_value("Role", "HD Customer", "home_page", "/helpdesk")
        frappe.db.set_value("Role", "HD Customer Manager", "home_page", "/helpdesk")
        self.run_patch().assert_called_once()
        settings = frappe.db.get_singles_dict("Portal Settings")
        self.assertFalse(settings.get("default_portal_home"))
        self.assertFalse(settings.get("default_role"))
        for role in ("HD Customer", "HD Customer Manager"):
            self.assertFalse(frappe.db.get_value("Role", role, "home_page"), role)

    def test_keeps_what_an_admin_set(self) -> None:
        self.set_portal_settings("/orders", "Customer")
        frappe.db.set_value("Role", "HD Customer", "home_page", "/orders")
        frappe.db.set_value("Role", "HD Customer Manager", "home_page", None)
        self.run_patch().assert_not_called()
        settings = frappe.db.get_singles_dict("Portal Settings")
        self.assertEqual(settings.get("default_portal_home"), "/orders")
        self.assertEqual(settings.get("default_role"), "Customer")
        self.assertEqual(
            frappe.db.get_value("Role", "HD Customer", "home_page"), "/orders"
        )
