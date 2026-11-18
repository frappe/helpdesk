import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import random_string

from helpdesk.integrations.whatsapp.account import add_ticket_action, creates_tickets
from helpdesk.integrations.whatsapp.test_utils import (
    make_whatsapp_account,
    requires_whatsapp,
)
from helpdesk.test_utils import make_agent_manager


@requires_whatsapp
class TestWhatsAppSettingsAccess(IntegrationTestCase):
    """The settings page writes WA Account and WA Settings through the standard API."""

    def test_only_system_managers_can_change_accounts_and_webhook_settings(
        self,
    ) -> None:
        manager = make_agent_manager("whatsapp-settings")
        for doctype in ("WA Account", "WA Settings"):
            for ptype in ("create", "write"):
                with self.subTest(doctype=doctype, ptype=ptype):
                    self.assertTrue(
                        frappe.has_permission(doctype, ptype, user="Administrator")
                    )
                    self.assertFalse(
                        frappe.has_permission(doctype, ptype, user=manager)
                    )


@requires_whatsapp
class TestWhatsAppAppendActions(IntegrationTestCase):
    """An HD Ticket row only turns Create tickets on; Helpdesk fills the ticket itself."""

    def tearDown(self) -> None:
        frappe.db.rollback()

    def test_only_an_hd_ticket_row_creates_tickets(self) -> None:
        self.assertTrue(creates_tickets(make_whatsapp_account()))
        account = make_whatsapp_account(
            append_actions=[append_action("Contact", "mobile_no", "first_name")]
        )
        rows = frappe.get_doc("WA Account", account).append_actions
        self.assertEqual([row.append_to for row in rows], ["Contact"])
        self.assertFalse(creates_tickets(account))

    def test_the_patch_turns_create_tickets_on_once_keeping_other_rows(self) -> None:
        account = make_whatsapp_account(
            append_actions=[append_action("Contact", "mobile_no", "first_name")]
        )
        add_ticket_action(account)
        add_ticket_action(account)
        rows = frappe.get_doc("WA Account", account).append_actions
        self.assertEqual([row.append_to for row in rows], ["Contact", "HD Ticket"])

    def test_an_account_connected_with_meta_creates_tickets(self) -> None:
        from whatsapp.whatsapp.oauth import _save_account

        phone_id = random_string(10)
        token = {
            "access_token": "meta-token",
            "app_id": "fc-app",
            "waba_id": random_string(10),
            "phone_id": phone_id,
            "pin": "123456",
            "webhook_secret": "route-secret",
        }
        self.assertEqual(_save_account(token, None), ("connected", phone_id))
        self.assertTrue(creates_tickets(phone_id))


def append_action(doctype: str, sender_field: str, sender_name_field: str) -> dict:
    return {
        "append_to": doctype,
        "trigger_on": "Incoming",
        "sender_field": sender_field,
        "sender_name_field": sender_name_field,
    }
