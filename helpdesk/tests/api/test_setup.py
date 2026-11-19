from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.api.setup import complete_setup, is_setup_pending
from helpdesk.patches.mark_existing_sites_set_up import execute as mark_existing_sites
from helpdesk.setup.welcome_ticket import AUTHOR_EMAIl
from helpdesk.test_utils import (
    as_non_v2_site,
    as_v2_site,
    create_agent,
    framework_setup_pending,
    make_ticket,
    unique_email,
    with_wizard_stages,
)

FRAMEWORK_SETUP = "frappe.desk.page.setup_wizard.setup_wizard.setup_complete"


class TestSetup(IntegrationTestCase):
    def setUp(self) -> None:
        frappe.set_user("Administrator")
        frappe.db.set_single_value("HD Settings", "setup_complete", 0)
        self.agent = create_agent(unique_email("setup-agent")).name

    def test_pending_for_system_manager_on_v2_site(self) -> None:
        with as_v2_site():
            self.assertTrue(is_setup_pending())

    def test_not_pending_off_v2_site(self) -> None:
        with as_non_v2_site():
            self.assertFalse(is_setup_pending())

    def test_not_pending_once_complete(self) -> None:
        frappe.db.set_single_value("HD Settings", "setup_complete", 1)
        with as_v2_site():
            self.assertFalse(is_setup_pending())

    def test_not_pending_for_agent(self) -> None:
        with as_v2_site(), self.set_user(self.agent):
            self.assertFalse(is_setup_pending())

    def test_sites_with_tickets_skip_setup(self) -> None:
        make_ticket()
        mark_existing_sites()
        with as_v2_site():
            self.assertFalse(is_setup_pending())

    def test_sites_with_only_the_welcome_ticket_keep_setup(self) -> None:
        with patch("frappe.db.count", return_value=1):
            mark_existing_sites()
        with as_v2_site():
            self.assertTrue(is_setup_pending())

    def test_complete_finishes_framework_setup_on_v2_site(self) -> None:
        with (
            as_v2_site(),
            framework_setup_pending(),
            with_wizard_stages([]),
            patch(FRAMEWORK_SETUP, return_value={"status": "ok"}) as framework_setup,
        ):
            complete_setup()
        framework_setup.assert_called_once()
        self.assertIn("timezone", framework_setup.call_args.args[0])
        self.assertTrue(frappe.db.get_single_value("HD Settings", "setup_complete"))

    def test_complete_returns_welcome_ticket(self) -> None:
        welcome = make_ticket(raised_by=AUTHOR_EMAIl).name
        with as_non_v2_site():
            self.assertEqual(complete_setup(), welcome)

    def test_complete_leaves_finished_framework_setup(self) -> None:
        with (
            as_v2_site(),
            patch("frappe.is_setup_complete", return_value=True),
            patch(FRAMEWORK_SETUP) as framework_setup,
        ):
            complete_setup()
        framework_setup.assert_not_called()
        self.assertTrue(frappe.db.get_single_value("HD Settings", "setup_complete"))

    def test_complete_leaves_framework_setup_off_v2_site(self) -> None:
        with (
            as_non_v2_site(),
            framework_setup_pending(),
            patch(FRAMEWORK_SETUP) as framework_setup,
        ):
            complete_setup()
        framework_setup.assert_not_called()

    def test_complete_leaves_framework_setup_to_wizard_stages(self) -> None:
        with (
            as_v2_site(),
            framework_setup_pending(),
            with_wizard_stages(["erpnext.stages"]),
            patch(FRAMEWORK_SETUP) as framework_setup,
        ):
            complete_setup()
        framework_setup.assert_not_called()

    def test_complete_ends_setup_when_framework_setup_fails(self) -> None:
        with (
            as_v2_site(),
            framework_setup_pending(),
            with_wizard_stages([]),
            patch(
                FRAMEWORK_SETUP, return_value={"status": "fail", "fail": "No region"}
            ),
            patch("frappe.log_error") as log_error,
        ):
            complete_setup()
        log_error.assert_called_once()
        self.assertTrue(frappe.db.get_single_value("HD Settings", "setup_complete"))

    def test_agent_cannot_complete_setup(self) -> None:
        with self.set_user(self.agent), self.assertRaises(frappe.PermissionError):
            complete_setup()
