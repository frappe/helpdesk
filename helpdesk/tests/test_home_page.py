import frappe
from frappe.tests import IntegrationTestCase
from frappe.website.utils import get_home_page

from helpdesk.test_utils import create_agent, unique_email


class TestHomePage(IntegrationTestCase):
    def home_page_for(self, user: str) -> str:
        frappe.cache.hdel("home_page", user)
        with self.set_user(user):
            return get_home_page()

    def test_guest_lands_on_portal(self):
        self.assertEqual(self.home_page_for("Guest"), "help")

    def test_agent_keeps_desk(self):
        agent = create_agent(unique_email("home-page-agent"))
        self.assertNotEqual(self.home_page_for(agent.name), "help")
