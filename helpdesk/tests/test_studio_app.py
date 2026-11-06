import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase
from frappe.utils import get_system_timezone, set_request

from helpdesk.helpdesk.doctype.hd_settings.helpers import get_customer_home_page
from helpdesk.helpdesk.hooks.studio_app import escape_for_shell, get_boot
from helpdesk.test_utils import make_agent, make_contact
from helpdesk.www.helpdesk.index import redirect_customer_home


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


class TestDeskRedirect(IntegrationTestCase):
    def tearDown(self) -> None:
        frappe.local.request = None
        frappe.set_user("Administrator")

    def redirect_for(self, user: str, page: str | None = None) -> str | None:
        frappe.set_user(user)
        query = {"redirect-to": page} if page else {}
        set_request(method="GET", path="/helpdesk", query_string=query)
        try:
            redirect_customer_home()
        except frappe.Redirect:
            return frappe.local.flags.redirect_location

    def test_a_customer_goes_back_to_the_login_page(self) -> None:
        customer = make_contact("redirect_customer")["user"]
        location = self.redirect_for(customer, "/help/articles/abc?a=1")
        self.assertTrue(location.endswith("/help/articles/abc?a=1"), location)

    def test_a_customer_with_no_page_goes_to_the_customer_home(self) -> None:
        customer = make_contact("redirect_customer_home")["user"]
        self.assertEqual(self.redirect_for(customer), get_customer_home_page())

    def test_a_customer_stays_on_this_site(self) -> None:
        customer = make_contact("redirect_customer_host")["user"]
        location = self.redirect_for(customer, "https://example.org/help")
        self.assertNotIn("example.org", location)

    def test_an_agent_stays_on_the_desk(self) -> None:
        agent = "redirect_agent@example.com"
        make_agent(agent)
        self.assertIsNone(self.redirect_for(agent, "/help/articles/abc"))

    def test_a_system_manager_stays_on_the_desk(self) -> None:
        self.assertIsNone(self.redirect_for("Administrator", "/help/articles/abc"))
