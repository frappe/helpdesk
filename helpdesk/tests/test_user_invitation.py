import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.overrides.user_invitation import HelpdeskUserInvitation

BRAND = "Acme Support"


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
