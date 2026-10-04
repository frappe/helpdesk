import imaplib
from typing import Any
from unittest.mock import MagicMock, patch

import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.api.auth import get_current_user_email_info, set_user_email_accounts
from helpdesk.api.settings.email import create_email_account
from helpdesk.test_utils import (
    create_agent,
    create_user,
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
        self.email_server.return_value.connect.side_effect = imaplib.IMAP4.error(
            "AUTHENTICATIONFAILED"
        )
        # the add form sends incoming off by default, credentials are still checked
        for enable_incoming in (1, 0):
            data = make_email_account_data("GMail", enable_incoming=enable_incoming)
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


class TestSetUserEmailAccounts(IntegrationTestCase):
    """Agents manage links to outgoing accounts only; other links stay."""

    def setUp(self) -> None:
        frappe.set_user("Administrator")
        self.enterContext(patch(f"{EMAIL_ACCOUNT_MODULE}.EmailServer"))
        self.agent = create_agent(unique_email("email-agent")).name
        self.support = self.make_account("Sendgrid", enable_incoming=0)
        self.sales = self.make_account("Sendgrid", enable_incoming=0)
        self.incoming_only = self.make_account("GMail", enable_outgoing=0)

    def test_agent_replaces_outgoing_links_and_keeps_other_links(self) -> None:
        user = frappe.get_doc("User", self.agent)
        user.append("user_emails", {"email_account": self.incoming_only})
        user.save()

        with self.set_user(self.agent):
            set_user_email_accounts([self.support])
            self.assertEqual(self.linked_accounts(), {self.incoming_only, self.support})
            # the settings screen lists only the outgoing links
            outgoing = get_current_user_email_info()["outgoing_emails"]
            self.assertEqual([row.email_account for row in outgoing], [self.support])

            set_user_email_accounts([self.sales, self.sales])
            self.assertEqual(self.linked_accounts(), {self.incoming_only, self.sales})

    def test_accounts_without_outgoing_email_are_not_linked(self) -> None:
        with self.set_user(self.agent):
            set_user_email_accounts([self.incoming_only, "No Such Account"])

        self.assertEqual(self.linked_accounts(), set())

    def test_non_agent_cannot_set_email_accounts(self) -> None:
        user = create_user(unique_email("not-an-agent")).name

        with self.set_user(user), self.assertRaises(frappe.PermissionError):
            set_user_email_accounts([self.support])

    def make_account(self, service: str, **overrides: Any) -> str:
        return create_email_account(make_email_account_data(service, **overrides))

    def linked_accounts(self) -> set[str]:
        return set(
            frappe.get_all(
                "User Email", filters={"parent": self.agent}, pluck="email_account"
            )
        )
