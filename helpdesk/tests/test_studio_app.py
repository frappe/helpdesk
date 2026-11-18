import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase
from frappe.utils import get_system_timezone

from helpdesk.helpdesk.hooks.studio_app import escape_for_shell, get_boot
from helpdesk.test_utils import make_contact


class TestPageShell(UnitTestCase):
    def test_a_brand_name_cannot_break_out_of_the_shell(self) -> None:
        # renderer.html prints it in <title> and inside a JS string
        escaped = escape_for_shell('Acme "Help" </title><script>\\\nx')
        for unsafe in ('"', "<", ">", "\\", "\n"):
            self.assertNotIn(unsafe, escaped)

    def test_an_empty_value_stays_empty(self) -> None:
        self.assertEqual(escape_for_shell(None), "")


class TestBoot(IntegrationTestCase):
    def tearDown(self) -> None:
        frappe.set_user("Administrator")

    def test_the_boot_carries_the_customer_timezone(self) -> None:
        customer = make_contact("boot_customer")["user"]
        frappe.db.set_value("User", customer, "time_zone", "Asia/Tokyo")
        frappe.set_user(customer)
        self.assertEqual(get_boot()["user_timezone"], "Asia/Tokyo")

    def test_without_a_timezone_the_boot_carries_the_system_one(self) -> None:
        customer = make_contact("boot_customer_without_zone")["user"]
        frappe.db.set_value("User", customer, "time_zone", None)
        frappe.db.set_value("User", "Guest", "time_zone", "Asia/Tokyo")
        for user in (customer, "Guest"):
            frappe.set_user(user)
            self.assertEqual(get_boot()["user_timezone"], get_system_timezone())
