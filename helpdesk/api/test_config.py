import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.api.config import get_config
from helpdesk.helpdesk.doctype.hd_form_script.hd_form_script import get_form_script
from helpdesk.test_utils import (
    create_agent,
    disable_public_knowledge_base,
    enable_public_knowledge_base,
    make_form_script,
)


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

    def test_knowledge_base_scripts_reach_guests_only_on_a_public_kb(self) -> None:
        make_form_script(self, "Test KB Script", "kb", apply_to_knowledge_base=True)
        make_form_script(
            self, "Test Portal Script", "portal", apply_to_customer_portal=True
        )
        was_public = frappe.db.get_single_value("HD Settings", "public_knowledge_base")
        self.addCleanup(
            frappe.db.set_single_value,
            "HD Settings",
            "public_knowledge_base",
            was_public,
        )
        frappe.set_user("Guest")
        self.addCleanup(frappe.set_user, "Administrator")

        enable_public_knowledge_base()
        scripts = get_config().kb_form_scripts
        self.assertTrue(any(script.endswith("// kb") for script in scripts))
        self.assertFalse(any(script.endswith("// portal") for script in scripts))

        disable_public_knowledge_base()
        self.assertNotIn("kb_form_scripts", get_config())
        frappe.set_user("Administrator")
        self.assertIn("kb_form_scripts", get_config())

    def test_knowledge_base_scripts_stay_off_the_ticket_pages(self) -> None:
        make_form_script(self, "Test KB Script", "kb", apply_to_knowledge_base=True)
        for portal in (False, True):
            scripts = get_form_script("HD Ticket", is_customer_portal=portal) or []
            self.assertFalse(any(script.endswith("// kb") for script in scripts))

    def test_only_those_who_can_write_hd_settings_may_edit_them(self) -> None:
        self.assertTrue(get_config().can_edit_settings)
        agent = create_agent("config-agent@example.com")
        frappe.set_user(agent.name)
        self.addCleanup(frappe.set_user, "Administrator")
        self.assertFalse(get_config().can_edit_settings)
