import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.api.auth import update_profile
from helpdesk.api.config import get_config
from helpdesk.test_utils import create_agent, create_contact, unique_email


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

    def test_only_those_who_can_write_hd_settings_may_edit_them(self) -> None:
        self.assertTrue(get_config().can_edit_settings)
        agent = create_agent(unique_email("config-agent"))
        with self.set_user(agent.name):
            self.assertFalse(get_config().can_edit_settings)
