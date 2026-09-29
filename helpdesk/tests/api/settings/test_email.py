import imaplib
from typing import Any
from unittest.mock import MagicMock, patch

import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.api.settings.email import create_email_account
from helpdesk.test_utils import (
    create_agent,
    make_agent_manager,
    make_email_account_data,
    unique_email,
)

EMAIL_ACCOUNT_MODULE = "frappe.email.doctype.email_account.email_account"


class TestCreateEmailAccount(IntegrationTestCase):
    def setUp(self) -> None:
        frappe.set_user("Administrator")
        self.email_server: MagicMock = self.enterContext(
            patch(f"{EMAIL_ACCOUNT_MODULE}.EmailServer")
        )

    def tearDown(self) -> None:
        frappe.set_user("Administrator")

    def test_gmail_account_saves_provider_servers_and_ticket_folder(self) -> None:
        name = create_email_account(make_email_account_data("GMail"))

        account = frappe.get_doc("Email Account", name)
        self.assertEqual(account.service, "GMail")
        self.assertEqual(account.email_server, "imap.gmail.com")
        self.assertEqual(account.smtp_server, "smtp.gmail.com")
        self.assertEqual((account.use_ssl, account.use_imap), (1, 1))
        self.assertEqual(account.create_contact, 1)
        self.assertEqual(account.get_password(), "app-password")
        self.assert_ticket_inbox_folder(account)
        self.email_server.return_value.connect.assert_called_once()

    def test_invalid_credentials_are_rejected_and_nothing_saved(self) -> None:
        data = make_email_account_data("GMail")
        self.email_server.return_value.connect.side_effect = imaplib.IMAP4.error(
            "AUTHENTICATIONFAILED"
        )

        with self.assertRaises(frappe.ValidationError):
            create_email_account(data)

        self.assertFalse(self.account_exists(data))

    def test_unsupported_or_missing_service_is_rejected(self) -> None:
        for service in ("Hotmail", "", None):
            data = make_email_account_data(service)
            with self.assertRaises(frappe.ValidationError):
                create_email_account(data)
            self.assertFalse(self.account_exists(data))

    def test_invalid_email_address_is_rejected(self) -> None:
        data = make_email_account_data("GMail", email_id="not-an-email")

        with self.assertRaises(frappe.ValidationError):
            create_email_account(data)

        self.assertFalse(self.account_exists(data))

    def test_custom_service_saves_given_servers_and_defaults(self) -> None:
        data = make_email_account_data(
            "Custom",
            email_server="imap.example.com",
            incoming_port="993",
            smtp_server="smtp.example.com",
            use_ssl=1,
        )

        account = frappe.get_doc("Email Account", create_email_account(data))

        self.assertEqual(account.service, "")
        self.assertEqual(account.email_server, "imap.example.com")
        self.assertEqual(account.incoming_port, "993")
        self.assertEqual(account.smtp_server, "smtp.example.com")
        self.assertEqual(account.smtp_port, "587")
        self.assertEqual((account.use_ssl, account.use_tls), (1, 0))
        self.assertEqual(account.validate_ssl_certificate, 1)
        self.assert_ticket_inbox_folder(account)

    def test_frappe_mail_saves_api_credentials_without_imap(self) -> None:
        data = make_email_account_data(
            "Frappe Mail",
            api_key="mail-key",
            api_secret="mail-secret",
            frappe_mail_site="https://mail.example.com",
        )

        with patch(
            f"{EMAIL_ACCOUNT_MODULE}.EmailAccount.validate_frappe_mail_settings"
        ) as validate_frappe_mail:
            name = create_email_account(data)

        account = frappe.get_doc("Email Account", name)
        self.assertEqual(account.use_imap, 0)
        self.assertEqual(account.append_to, "HD Ticket")
        self.assertEqual(account.api_key, "mail-key")
        self.assertEqual(account.get_password("api_secret"), "mail-secret")
        self.assertEqual(account.frappe_mail_site, "https://mail.example.com")
        validate_frappe_mail.assert_called()
        self.email_server.assert_not_called()

    def test_outgoing_only_sendgrid_account_is_created(self) -> None:
        data = make_email_account_data("Sendgrid", enable_incoming=0)

        account = frappe.get_doc("Email Account", create_email_account(data))

        self.assertEqual(account.smtp_server, "smtp.sendgrid.net")
        self.assertEqual(account.enable_outgoing, 1)
        self.email_server.assert_not_called()

    def test_outlook_yahoo_and_yandex_accounts_are_created(self) -> None:
        for service in ("Outlook", "Yahoo", "Yandex"):
            data = make_email_account_data(service)
            create_email_account(data)
            self.assertTrue(self.account_exists(data))

    def test_agent_cannot_create_email_account(self) -> None:
        agent = create_agent(unique_email("email-agent"))
        data = make_email_account_data("GMail")

        with self.set_user(agent.name), self.assertRaises(frappe.PermissionError):
            create_email_account(data)

        self.assertFalse(self.account_exists(data))

    def test_agent_manager_can_create_outgoing_email_account(self) -> None:
        data = make_email_account_data("GMail", enable_incoming=0)

        with self.set_user(make_agent_manager("email-manager")):
            create_email_account(data)

        self.assertTrue(self.account_exists(data))

    def account_exists(self, data: dict[str, Any]) -> bool:
        return bool(
            frappe.db.exists("Email Account", {"email_id": data["email_id"]})
            or frappe.db.exists("Email Account", data["email_account_name"])
        )

    def assert_ticket_inbox_folder(self, account) -> None:
        folders = [(row.folder_name, row.append_to) for row in account.imap_folder]
        self.assertEqual(folders, [("INBOX", "HD Ticket")])
