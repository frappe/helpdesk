import frappe
from frappe.tests.utils import FrappeTestCase

from helpdesk.api.permission import has_app_permission
from helpdesk.test_utils import create_agent


class TestPermission(FrappeTestCase):
    website_user = "helpdesk-website-user@example.com"
    manager_user = "helpdesk-manager@example.com"
    original_user = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.original_user = frappe.session.user

    def tearDown(self):
        frappe.set_user(self.original_user or "Administrator")

    def test_agent_can_access_helpdesk_app(self):
        create_agent("helpdesk-agent@example.com")

        frappe.set_user("helpdesk-agent@example.com")

        self.assertTrue(has_app_permission())

    def test_agent_manager_can_access_helpdesk_app(self):
        user = self._get_or_create_user(self.manager_user)
        user.add_roles("Agent Manager")

        frappe.set_user(self.manager_user)

        self.assertTrue(has_app_permission())

    def test_regular_website_user_cannot_access_helpdesk_app(self):
        self._get_or_create_user(self.website_user)

        frappe.set_user(self.website_user)

        self.assertFalse(has_app_permission())

    def _get_or_create_user(self, email):
        if frappe.db.exists("User", email):
            return frappe.get_doc("User", email)

        return frappe.get_doc(
            {
                "doctype": "User",
                "email": email,
                "first_name": email.split("@")[0],
                "send_welcome_email": 0,
            }
        ).insert(ignore_permissions=True)
