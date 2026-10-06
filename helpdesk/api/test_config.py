import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.api.config import get_config
from helpdesk.test_utils import create_agent


class TestConfig(IntegrationTestCase):
    """Guest-readable settings; the signed-out topbar is drawn from them."""

    def test_a_guest_gets_every_field_and_their_own_name(self) -> None:
        frappe.set_user("Guest")
        self.addCleanup(frappe.set_user, "Administrator")
        config = get_config()
        self.assertEqual(config.session_user, "Guest")
        self.assertFalse(config.is_agent)
        self.assertFalse(config.can_edit_settings)
        self.assertIn("confirm_resolution_after_days", config)
        self.assertTrue(config.date_format)

    def test_only_those_who_can_write_hd_settings_may_edit_them(self) -> None:
        self.assertTrue(get_config().can_edit_settings)
        agent = create_agent("config-agent@example.com")
        frappe.set_user(agent.name)
        self.addCleanup(frappe.set_user, "Administrator")
        self.assertFalse(get_config().can_edit_settings)
