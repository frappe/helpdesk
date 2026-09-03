from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from helpdesk.overrides.email_account import CustomEmailAccount


class TestCustomEmailAccountInboundMails(FrappeTestCase):
    def base_email_account(self):
        """A CustomEmailAccount instance built from the shared "_Test Comm Account 1" fixture."""
        account = CustomEmailAccount(
            frappe.get_doc("Email Account", "_Test Comm Account 1").as_dict()
        )
        account.enable_incoming = 1
        account.use_imap = 1
        return account

    def test_get_inbound_mails_skips_folder_loop_when_incoming_server_returns_none(self):
        # @dokos: get_inbound_mails must not call select_imap_folder on a connection that
        # failed to authenticate - that's what produced the confusing NONAUTH SELECT error.
        email_account = self.base_email_account()

        with (
            patch.object(email_account, "get_incoming_server", return_value=None),
            patch("frappe.email.receive.EmailServer.select_imap_folder") as mocked_select,
        ):
            mails = email_account.get_inbound_mails()

        self.assertEqual(mails, [])
        mocked_select.assert_not_called()
