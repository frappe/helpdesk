import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.api.config import get_config


class TestConfig(IntegrationTestCase):
    """Guest-readable settings; the signed-out topbar is drawn from them."""

    def test_a_guest_gets_every_field_and_their_own_name(self) -> None:
        frappe.set_user("Guest")
        self.addCleanup(frappe.set_user, "Administrator")
        config = get_config()
        self.assertEqual(config.session_user, "Guest")
        self.assertFalse(config.is_agent)
        self.assertIn("confirm_resolution_after_days", config)
        self.assertTrue(config.date_format)
