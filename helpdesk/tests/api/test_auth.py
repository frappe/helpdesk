import frappe
from frappe.tests import IntegrationTestCase
from frappe.tests.utils import change_settings

from helpdesk.api.auth import update_profile
from helpdesk.api.config import get_config
from helpdesk.helpdesk.doctype.hd_form_script.hd_form_script import get_form_script
from helpdesk.test_utils import (
    create_agent,
    create_contact,
    make_form_script,
    unique_email,
)


class TestUpdateProfile(IntegrationTestCase):
    """A portal user editing their own name and picture."""

    def setUp(self) -> None:
        self.person = create_contact("Profile Owner", unique_email("profile-owner"))
        self.enterContext(self.set_user(self.person["user"]))

    def test_the_name_reaches_the_user_and_the_contact(self) -> None:
        update_profile(first_name="Renamed", last_name="Person")

        self.assertEqual(
            frappe.db.get_value("User", self.person["user"], "full_name"),
            "Renamed Person",
        )
        self.assertEqual(
            frappe.db.get_value("Contact", self.person["contact"], "first_name"),
            "Renamed",
        )

    def test_an_uploaded_picture_is_kept(self) -> None:
        update_profile(image="/files/me.png")

        self.assertEqual(
            frappe.db.get_value("User", self.person["user"], "user_image"),
            "/files/me.png",
        )

    def test_language_and_time_zone_are_saved(self) -> None:
        update_profile(language="en", time_zone="Asia/Kolkata")

        self.assertEqual(
            frappe.db.get_value("User", self.person["user"], ["language", "time_zone"]),
            ("en", "Asia/Kolkata"),
        )

    def test_a_linked_picture_is_refused(self) -> None:
        with self.assertRaises(frappe.ValidationError):
            update_profile(image="https://tracker.example.com/pixel.png")


class TestConfig(IntegrationTestCase):
    """Guest-readable settings; the signed-out topbar is drawn from them."""

    def test_a_guest_gets_every_field_and_their_own_name(self) -> None:
        with self.set_user("Guest"):
            config = get_config()
        self.assertEqual(config.session_user, "Guest")
        self.assertFalse(config.is_agent)
        self.assertFalse(config.can_edit_settings)
        self.assertTrue(config.date_format)

    def test_knowledge_base_scripts_reach_guests_only_on_a_public_kb(self) -> None:
        make_form_script(self, "Test KB Script", "kb", apply_to_knowledge_base=True)
        make_form_script(
            self, "Test Portal Script", "portal", apply_to_customer_portal=True
        )

        with change_settings("HD Settings", {"public_knowledge_base": 1}):
            with self.set_user("Guest"):
                scripts = get_config().knowledge_base_form_scripts
            self.assertTrue(any(script.endswith("// kb") for script in scripts))
            self.assertFalse(any(script.endswith("// portal") for script in scripts))

        with change_settings("HD Settings", {"public_knowledge_base": 0}):
            with self.set_user("Guest"):
                self.assertNotIn("knowledge_base_form_scripts", get_config())
            self.assertIn("knowledge_base_form_scripts", get_config())

    def test_knowledge_base_scripts_stay_off_the_ticket_pages(self) -> None:
        make_form_script(self, "Test KB Script", "kb", apply_to_knowledge_base=True)
        for portal in (False, True):
            scripts = get_form_script("HD Ticket", is_customer_portal=portal) or []
            self.assertFalse(any(script.endswith("// kb") for script in scripts))

    def test_only_those_who_can_write_hd_settings_may_edit_them(self) -> None:
        self.assertTrue(get_config().can_edit_settings)
        agent = create_agent(unique_email("config-agent"))
        with self.set_user(agent.name):
            self.assertFalse(get_config().can_edit_settings)
