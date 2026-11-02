from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.api.banners import BANNERS, get_banners, refresh_trial
from helpdesk.test_utils import (
    clear_trial_cache,
    create_agent,
    create_contact,
    dismiss_banner_as,
    fake_cloud_settings,
    make_agent_manager,
    show_only_banners,
    unique_email,
)

PORTAL_BANNER = "customer_portal_permission"
FIELD_BANNER = "ticket_field_permission"


def banner_names() -> list[str]:
    return [banner["name"] for banner in get_banners()]


CLOUD_SETTINGS = "helpdesk.integrations.frappe_cloud.cloud_settings"


class TestBanners(IntegrationTestCase):
    def setUp(self) -> None:
        frappe.set_user("Administrator")
        # Not a Frappe Cloud site, whatever the test site's config says
        self.enterContext(patch(CLOUD_SETTINGS, None))

    def test_manager_sees_only_banners_that_are_on(self) -> None:
        manager = make_agent_manager("banner-manager")
        show_only_banners(PORTAL_BANNER)
        with self.set_user(manager):
            self.assertEqual(banner_names(), [PORTAL_BANNER])

    def test_flag_never_saved_counts_as_off(self) -> None:
        # the patches set only their own flag, so an upgraded site can lack a row
        show_only_banners(FIELD_BANNER)
        frappe.db.delete(
            "Singles", {"doctype": "HD Settings", "field": BANNERS[PORTAL_BANNER]}
        )
        self.assertEqual(banner_names(), [FIELD_BANNER])

    def test_agents_and_customers_see_no_banners(self) -> None:
        agent = create_agent(unique_email("banner-agent")).name
        customer = create_contact("Banner Customer", unique_email("banner-customer"))
        show_only_banners(PORTAL_BANNER, FIELD_BANNER)
        for user in (agent, customer["user"]):
            with self.subTest(user=user), self.set_user(user):
                self.assertEqual(banner_names(), [])

    def test_dismissing_hides_the_banner_and_notifies_clients(self) -> None:
        show_only_banners(PORTAL_BANNER, FIELD_BANNER)
        publish_realtime = dismiss_banner_as("Administrator", FIELD_BANNER)

        self.assertEqual(banner_names(), [PORTAL_BANNER])
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
        self.assertEqual(banner_names(), [PORTAL_BANNER])


ACTIVE_TRIAL = {"state": "Active", "days_left": 10}
ENDED_TRIAL = {"state": "Ended", "days_left": 0}


class TestTrialBanner(IntegrationTestCase):
    def setUp(self) -> None:
        frappe.set_user("Administrator")
        show_only_banners()
        clear_trial_cache("Administrator")
        self.addCleanup(clear_trial_cache, "Administrator")

    def use_cloud(self, trial: dict | None):
        return self.enterContext(patch(CLOUD_SETTINGS, fake_cloud_settings(trial)))

    def trial_banner(self) -> dict | None:
        return next((b for b in get_banners() if b["name"] == "trial"), None)

    def test_trial_is_read_once_and_cached(self) -> None:
        cloud_settings = self.use_cloud(ACTIVE_TRIAL)
        self.assertEqual(self.trial_banner(), {"name": "trial", "trial": ACTIVE_TRIAL})
        self.trial_banner()
        cloud_settings.get_billing.assert_called_once()

    def test_failed_read_keeps_last_trial_and_retries_soon(self) -> None:
        cloud_settings = self.use_cloud(ACTIVE_TRIAL)
        with self.freeze_time("2026-11-02 10:00:00"):
            self.trial_banner()
        cloud_settings.get_billing.side_effect = frappe.ValidationError
        with self.freeze_time("2026-11-02 17:00:00"):
            self.assertEqual(self.trial_banner()["trial"], ACTIVE_TRIAL)
        with self.freeze_time("2026-11-02 17:06:00"):
            self.trial_banner()
        self.assertEqual(cloud_settings.get_billing.call_count, 3)

    def test_refresh_reads_the_trial_again(self) -> None:
        cloud_settings = self.use_cloud(ACTIVE_TRIAL)
        self.trial_banner()
        cloud_settings.get_billing.return_value = {"trial": None}
        refresh_trial()
        self.assertIsNone(self.trial_banner())

    def test_dismissing_hides_an_active_trial_for_that_user(self) -> None:
        self.use_cloud(ACTIVE_TRIAL)
        publish_realtime = dismiss_banner_as("Administrator", "trial")
        self.assertIsNone(self.trial_banner())
        self.assertEqual(publish_realtime.call_args.kwargs["user"], "Administrator")

    def test_ended_trial_cannot_be_dismissed(self) -> None:
        self.use_cloud(ENDED_TRIAL)
        dismiss_banner_as("Administrator", "trial")
        self.assertEqual(self.trial_banner()["trial"], ENDED_TRIAL)

    def test_no_trial_without_cloud_settings(self) -> None:
        self.use_cloud(ACTIVE_TRIAL).is_cloud_settings_enabled.return_value = False
        self.assertIsNone(self.trial_banner())

    def test_agents_cannot_refresh_the_trial(self) -> None:
        agent = create_agent(unique_email("trial-agent")).name
        with self.set_user(agent), self.assertRaises(frappe.PermissionError):
            refresh_trial()
