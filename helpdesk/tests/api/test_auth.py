from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.api.auth import get_current_user_email_info, set_user_email_accounts
from helpdesk.test_utils import (
    create_agent,
    create_user,
    get_linked_email_accounts,
    make_email_account,
    unique_email,
)

EMAIL_ACCOUNT_MODULE = "frappe.email.doctype.email_account.email_account"


class TestSetUserEmailAccounts(IntegrationTestCase):
    """Agents manage links to outgoing accounts only; other links stay."""

    def setUp(self) -> None:
        frappe.set_user("Administrator")
        self.enterContext(patch(f"{EMAIL_ACCOUNT_MODULE}.EmailServer"))
        self.agent = create_agent(unique_email("email-agent")).name
        self.support = make_email_account(enable_incoming=0)
        self.sales = make_email_account(enable_incoming=0)
        self.incoming_only = make_email_account(enable_outgoing=0)

    def test_agent_replaces_outgoing_links_and_keeps_other_links(self) -> None:
        user = frappe.get_doc("User", self.agent)
        user.append("user_emails", {"email_account": self.incoming_only})
        user.save()

        with self.set_user(self.agent):
            set_user_email_accounts([self.support])
            self.assertEqual(
                get_linked_email_accounts(self.agent),
                {self.incoming_only, self.support},
            )
            # the settings screen lists only the outgoing links
            outgoing = get_current_user_email_info()["outgoing_emails"]
            self.assertEqual([row.email_account for row in outgoing], [self.support])

            set_user_email_accounts([self.sales, self.sales])
            self.assertEqual(
                get_linked_email_accounts(self.agent), {self.incoming_only, self.sales}
            )

    def test_accounts_without_outgoing_email_are_not_linked(self) -> None:
        with self.set_user(self.agent):
            set_user_email_accounts([self.incoming_only, "No Such Account"])

        self.assertEqual(get_linked_email_accounts(self.agent), set())

    def test_non_agent_cannot_set_email_accounts(self) -> None:
        user = create_user(unique_email("not-an-agent")).name

        with self.set_user(user), self.assertRaises(frappe.PermissionError):
            set_user_email_accounts([self.support])
