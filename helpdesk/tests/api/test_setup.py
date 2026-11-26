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
    make_ticket,
    unique_email,
)


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

    def test_complete_returns_welcome_ticket(self) -> None:
        frappe.db.delete("HD Ticket", {"raised_by": AUTHOR_EMAIl})
        welcome = make_ticket(raised_by=AUTHOR_EMAIl).name
        with as_non_v2_site():
            self.assertEqual(complete_setup(), welcome)

    def test_agent_cannot_complete_setup(self) -> None:
        with self.set_user(self.agent), self.assertRaises(frappe.PermissionError):
            complete_setup()
