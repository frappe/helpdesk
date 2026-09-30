from unittest.mock import MagicMock, patch

import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.api.banners import BANNERS, dismiss_banner, get_banners
from helpdesk.test_utils import (
    create_agent,
    create_contact,
    make_agent_manager,
    unique_email,
)

PORTAL_BANNER = "customer_portal_permission"
FIELD_BANNER = "ticket_field_permission"


class TestBanners(IntegrationTestCase):
    def setUp(self) -> None:
        frappe.set_user("Administrator")

    def test_manager_sees_only_banners_that_are_on(self) -> None:
        manager = make_agent_manager("banner-manager")
        with self.banners_on(PORTAL_BANNER), self.set_user(manager):
            self.assertEqual(get_banners(), [PORTAL_BANNER])

    def test_agents_and_customers_see_no_banners(self) -> None:
        agent = create_agent(unique_email("banner-agent")).name
        customer = create_contact("Banner Customer", unique_email("banner-customer"))
        with self.banners_on(PORTAL_BANNER, FIELD_BANNER):
            for user in (agent, customer["user"]):
                with self.subTest(user=user), self.set_user(user):
                    self.assertEqual(get_banners(), [])

    def test_dismissing_hides_the_banner_and_notifies_clients(self) -> None:
        with self.banners_on(PORTAL_BANNER, FIELD_BANNER):
            publish_realtime = self.dismiss_as("Administrator", FIELD_BANNER)
            self.assertEqual(get_banners(), [PORTAL_BANNER])

        publish_realtime.assert_called_once()
        self.assertEqual(
            publish_realtime.call_args.args[0], "helpdesk:settings-updated"
        )

    def test_unknown_banner_is_rejected(self) -> None:
        with self.assertRaises(frappe.ValidationError):
            self.dismiss_as("Administrator", "no_such_banner")

    def test_agents_and_customers_cannot_dismiss(self) -> None:
        agent = create_agent(unique_email("dismiss-agent")).name
        customer = create_contact("Dismiss Customer", unique_email("dismiss-cust"))
        with self.banners_on(PORTAL_BANNER):
            for user in (agent, customer["user"]):
                with self.subTest(user=user), self.assertRaises(frappe.PermissionError):
                    self.dismiss_as(user, PORTAL_BANNER)
            self.assertEqual(get_banners(), [PORTAL_BANNER])

    def banners_on(self, *banners: str):
        """Turn on exactly `banners` for the duration of the block."""
        return self.change_settings(
            "HD Settings",
            {flag: int(banner in banners) for banner, flag in BANNERS.items()},
        )

    def dismiss_as(self, user: str, banner: str) -> MagicMock:
        """Dismiss `banner` as `user`, returning the realtime publisher mock."""
        with patch("frappe.publish_realtime") as publish_realtime, self.set_user(user):
            dismiss_banner(banner)
        return publish_realtime
