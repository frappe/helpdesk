import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.api.onboarding import mark_persona_captured
from helpdesk.overrides.user_invitation import HelpdeskUserInvitation

BRAND = "Acme Support"


class TestMarkPersonaCaptured(IntegrationTestCase):
    def setUp(self) -> None:
        frappe.set_user("Administrator")
        frappe.db.set_single_value("HD Settings", "brand_name", "")
        frappe.db.set_single_value("HD Settings", "persona_captured", 0)
        frappe.db.set_single_value("Website Settings", "app_name", "")
        frappe.db.set_default("site_name", "")

    def tearDown(self) -> None:
        frappe.db.rollback()

    def test_brand_name_written_to_settings(self):
        mark_persona_captured(brand_name=BRAND)
        self.assertEqual(frappe.db.get_single_value("HD Settings", "brand_name"), BRAND)
        self.assertEqual(
            frappe.db.get_single_value("Website Settings", "app_name"), BRAND
        )

    def test_site_name_set_for_welcome_email_subject(self):
        # Frappe builds the welcome email subject as "Welcome to <site_name>".
        mark_persona_captured(brand_name=BRAND)
        self.assertEqual(frappe.db.get_default("site_name"), BRAND)

    def test_persona_captured_flag_set(self):
        mark_persona_captured()
        self.assertTrue(frappe.db.get_single_value("HD Settings", "persona_captured"))

    def test_blank_brand_leaves_brand_untouched(self):
        mark_persona_captured(brand_name="   ")
        self.assertTrue(frappe.db.get_single_value("HD Settings", "persona_captured"))
        self.assertFalse(frappe.db.get_single_value("HD Settings", "brand_name"))


class TestInvitationTitleOverride(IntegrationTestCase):
    def setUp(self) -> None:
        frappe.set_user("Administrator")
        frappe.db.set_single_value("HD Settings", "brand_name", "")

    def tearDown(self) -> None:
        frappe.db.rollback()

    def _invitation(self) -> HelpdeskUserInvitation:
        invitation = frappe.new_doc("User Invitation")
        invitation.app_name = "helpdesk"
        return invitation

    def test_override_is_registered(self):
        self.assertIsInstance(frappe.new_doc("User Invitation"), HelpdeskUserInvitation)

    def test_title_uses_brand_name(self):
        # Subject becomes "You've been invited to join <brand> on <app title>".
        frappe.db.set_single_value("HD Settings", "brand_name", BRAND)
        app_title = frappe.get_hooks("app_title", app_name="helpdesk")[0]
        self.assertEqual(
            self._invitation()._get_email_title(), f"{BRAND} on {app_title}"
        )

    def test_title_falls_back_to_app_title(self):
        self.assertEqual(
            self._invitation()._get_email_title(),
            frappe.get_hooks("app_title", app_name="helpdesk")[0],
        )

    def test_other_apps_keep_their_title(self):
        # The override is site-wide; a brand name must not leak into other
        # apps' invitation emails.
        frappe.db.set_single_value("HD Settings", "brand_name", BRAND)
        invitation = frappe.new_doc("User Invitation")
        invitation.app_name = "frappe"
        self.assertEqual(
            invitation._get_email_title(),
            frappe.get_hooks("app_title", app_name="frappe")[0],
        )
