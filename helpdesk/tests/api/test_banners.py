import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.api.banners import BANNERS, get_banners
from helpdesk.test_utils import (
    create_agent,
    create_contact,
    dismiss_banner_as,
    make_agent_manager,
    show_only_banners,
    unique_email,
)

PORTAL_BANNER = "customer_portal_permission"
FIELD_BANNER = "ticket_field_permission"


class TestBanners(IntegrationTestCase):
    def setUp(self) -> None:
        frappe.set_user("Administrator")

    def test_manager_sees_only_banners_that_are_on(self) -> None:
        manager = make_agent_manager("banner-manager")
        show_only_banners(PORTAL_BANNER)
        with self.set_user(manager):
            self.assertEqual(get_banners(), [PORTAL_BANNER])

    def test_flag_never_saved_counts_as_off(self) -> None:
        # the patches set only their own flag, so an upgraded site can lack a row
        show_only_banners(FIELD_BANNER)
        frappe.db.delete(
            "Singles", {"doctype": "HD Settings", "field": BANNERS[PORTAL_BANNER]}
        )
        self.assertEqual(get_banners(), [FIELD_BANNER])

    def test_agents_and_customers_see_no_banners(self) -> None:
        agent = create_agent(unique_email("banner-agent")).name
        customer = create_contact("Banner Customer", unique_email("banner-customer"))
        show_only_banners(PORTAL_BANNER, FIELD_BANNER)
        for user in (agent, customer["user"]):
            with self.subTest(user=user), self.set_user(user):
                self.assertEqual(get_banners(), [])

    def test_dismissing_hides_the_banner_and_notifies_clients(self) -> None:
        show_only_banners(PORTAL_BANNER, FIELD_BANNER)
        publish_realtime = dismiss_banner_as("Administrator", FIELD_BANNER)

        self.assertEqual(get_banners(), [PORTAL_BANNER])
        publish_realtime.assert_called_once()
        self.assertEqual(
            publish_realtime.call_args.args[0], "helpdesk:settings-updated"
        )

    def test_unknown_banner_is_rejected(self) -> None:
        with self.assertRaises(frappe.ValidationError):
            dismiss_banner_as("Administrator", "no_such_banner")

    def test_agents_and_customers_cannot_dismiss(self) -> None:
        agent = create_agent(unique_email("dismiss-agent")).name
        customer = create_contact("Dismiss Customer", unique_email("dismiss-cust"))
        show_only_banners(PORTAL_BANNER)
        for user in (agent, customer["user"]):
            with self.subTest(user=user), self.assertRaises(frappe.PermissionError):
                dismiss_banner_as(user, PORTAL_BANNER)
        self.assertEqual(get_banners(), [PORTAL_BANNER])
