import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.api.config import get_config


class TestConfig(IntegrationTestCase):
    """The portal's only guest-readable endpoint: the whole signed-out experience —
    whether "Log in" shows, whether a ticket may be raised — is drawn from it."""

    def tearDown(self):
        frappe.set_user("Administrator")

    def test_it_is_reachable_without_a_session(self):
        # The portal renders for signed-out visitors; an endpoint that quietly stops
        # being guest-callable takes the whole topbar with it.
        self.assertIn(get_config, frappe.guest_methods)

    def test_it_names_the_session_user(self):
        frappe.set_user("Guest")

        self.assertEqual(get_config().session_user, "Guest")

    def test_it_names_a_signed_in_user(self):
        self.assertEqual(get_config().session_user, "Administrator")
