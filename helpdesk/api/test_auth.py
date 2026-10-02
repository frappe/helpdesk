import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.api.auth import update_profile
from helpdesk.test_utils import create_contact


class TestUpdateProfile(IntegrationTestCase):
    """A portal user editing their own name and picture."""

    def setUp(self) -> None:
        self.person = create_contact("Profile Owner", "owner@profile.test")
        frappe.set_user(self.person["user"])
        self.addCleanup(frappe.set_user, "Administrator")

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

    def test_a_linked_picture_is_refused(self) -> None:
        with self.assertRaises(frappe.ValidationError):
            update_profile(image="https://tracker.example.com/pixel.png")
