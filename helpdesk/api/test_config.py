import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.api.config import get_config, service_icon
from helpdesk.helpdesk.doctype.hd_form_script.hd_form_script import get_form_script
from helpdesk.test_utils import (
    disable_public_knowledge_base,
    enable_public_knowledge_base,
    make_form_script,
    set_portal_header_links,
)


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

    def test_a_guest_gets_the_header_links_in_order(self) -> None:
        set_portal_header_links(
            [
                {"label": "Contact sales", "url": "https://example.com/sales"},
                {"label": "Status", "url": "/status", "open_in_new_tab": 1},
            ]
        )
        self.addCleanup(set_portal_header_links, [])
        frappe.set_user("Guest")
        self.addCleanup(frappe.set_user, "Administrator")
        links = get_config().header_links
        self.assertEqual([link.label for link in links], ["Contact sales", "Status"])
        self.assertEqual(links[1].url, "/status")
        self.assertTrue(links[1].open_in_new_tab)

    def test_links_to_known_services_get_their_icon(self) -> None:
        self.assertEqual(service_icon("https://github.com/frappe/helpdesk"), "github")
        self.assertEqual(service_icon("https://www.youtube.com/@frappe"), "youtube")
        self.assertEqual(service_icon("https://twitter.com/frappetech"), "x")
        for url in (
            "https://notgithub.com",
            "https://github.com.example.com",
            "/kb/help",
        ):
            self.assertIsNone(service_icon(url))

    def test_header_links_accept_only_web_mail_and_site_urls(self) -> None:
        settings = frappe.get_single("HD Settings")
        for url in ("https://example.com", "mailto:help@example.com", "/kb/help"):
            settings.set("portal_header_links", [{"label": "Ok", "url": url}])
            settings.validate_header_links()
        for url in ("javascript:alert(1)", " JavaScript:alert(1)", "data:text/html,hi"):
            settings.set("portal_header_links", [{"label": "Bad", "url": url}])
            self.assertRaises(frappe.ValidationError, settings.validate_header_links)
        settings.set("portal_header_links", [{"label": "", "url": "/kb"}])
        self.assertRaises(frappe.ValidationError, settings.validate_header_links)

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
