from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.api.setup import (
    can_send_email,
    complete_setup,
    is_setup_pending,
    reset_setup,
)
from helpdesk.patches.mark_existing_sites_set_up import execute as mark_existing_sites
from helpdesk.test_utils import as_v2_site, create_agent, unique_email

FRAMEWORK_SETUP = "frappe.desk.page.setup_wizard.setup_wizard.setup_complete"


class TestSetup(IntegrationTestCase):
    def setUp(self) -> None:
        frappe.set_user("Administrator")
        frappe.db.set_single_value("HD Settings", "setup_complete", 0)
        self.agent = create_agent(unique_email("setup-agent")).name

    def not_v2_site(self):
        return patch.dict(
            frappe.local.conf, {"pilot_endpoint": None, "pilot_auth_token": None}
        )

    def framework_setup_pending(self):
        return patch("frappe.is_setup_complete", return_value=False)

    def test_pending_for_system_manager_on_v2_site(self) -> None:
        with as_v2_site():
            self.assertTrue(is_setup_pending())

    def test_not_pending_off_v2_site(self) -> None:
        with self.not_v2_site():
            self.assertFalse(is_setup_pending())

    def test_not_pending_once_complete(self) -> None:
        frappe.db.set_single_value("HD Settings", "setup_complete", 1)
        with as_v2_site():
            self.assertFalse(is_setup_pending())

    def test_not_pending_for_agent(self) -> None:
        with as_v2_site(), self.set_user(self.agent):
            self.assertFalse(is_setup_pending())

    def test_existing_sites_skip_setup(self) -> None:
        mark_existing_sites()
        with as_v2_site():
            self.assertFalse(is_setup_pending())

    def test_complete_finishes_framework_setup_on_v2_site(self) -> None:
        with (
            as_v2_site(),
            self.framework_setup_pending(),
            patch(FRAMEWORK_SETUP, return_value={"status": "ok"}) as framework_setup,
        ):
            complete_setup()
        framework_setup.assert_called_once()
        self.assertIn("timezone", framework_setup.call_args.args[0])
        self.assertTrue(frappe.db.get_single_value("HD Settings", "setup_complete"))

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
            self.not_v2_site(),
            self.framework_setup_pending(),
            patch(FRAMEWORK_SETUP) as framework_setup,
        ):
            complete_setup()
        framework_setup.assert_not_called()

    def test_complete_leaves_framework_setup_to_wizard_stages(self) -> None:
        hooks = frappe.get_hooks
        with (
            as_v2_site(),
            self.framework_setup_pending(),
            patch(
                "frappe.get_hooks",
                side_effect=lambda hook=None, *a, **kw: (
                    ["erpnext.stages"]
                    if hook == "setup_wizard_stages"
                    else hooks(hook, *a, **kw)
                ),
            ),
            patch(FRAMEWORK_SETUP) as framework_setup,
        ):
            complete_setup()
        framework_setup.assert_not_called()

    def test_complete_ends_setup_when_framework_setup_fails(self) -> None:
        with (
            as_v2_site(),
            self.framework_setup_pending(),
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

    def test_can_send_email_follows_outgoing_account(self) -> None:
        find = "frappe.email.doctype.email_account.email_account.EmailAccount.find_default_outgoing"
        with patch(find, return_value=None):
            self.assertFalse(can_send_email())
        with patch(find, return_value=frappe._dict(name="Support")):
            self.assertTrue(can_send_email())

    def test_agent_cannot_check_email_sending(self) -> None:
        with self.set_user(self.agent), self.assertRaises(frappe.PermissionError):
            can_send_email()


class TestResetSetup(IntegrationTestCase):
    def setUp(self) -> None:
        frappe.set_user("Administrator")
        frappe.db.set_single_value("HD Settings", "setup_complete", 1)

    def developer_mode(self, on: bool):
        return patch.dict(frappe.local.conf, {"developer_mode": int(on)})

    def test_reset_shows_setup_again(self) -> None:
        frappe.db.set_single_value("System Settings", "enable_telemetry", 0)
        with self.developer_mode(True):
            reset_setup()
        self.assertFalse(frappe.db.get_single_value("HD Settings", "setup_complete"))
        self.assertTrue(
            frappe.db.get_single_value("System Settings", "enable_telemetry")
        )
        self.assertFalse(frappe.is_setup_complete())
        with as_v2_site():
            self.assertTrue(is_setup_pending())

    def test_reset_refused_outside_developer_mode(self) -> None:
        with self.developer_mode(False), self.assertRaises(frappe.PermissionError):
            reset_setup()
        self.assertTrue(frappe.db.get_single_value("HD Settings", "setup_complete"))

    def test_agent_cannot_reset_setup(self) -> None:
        agent = create_agent(unique_email("reset-agent")).name
        with (
            self.developer_mode(True),
            self.set_user(agent),
            self.assertRaises(frappe.PermissionError),
        ):
            reset_setup()
