import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.consts import WELCOME_TICKET_SUBJECT
from helpdesk.patches.mark_setup_complete_for_existing_sites import execute
from helpdesk.test_utils import make_email_account, make_ticket


class TestExistingSitePatch(IntegrationTestCase):
    def setUp(self) -> None:
        frappe.db.set_single_value("HD Settings", "setup_complete", 0)
        for ticket in frappe.get_all(
            "HD Ticket", filters={"subject": ["!=", WELCOME_TICKET_SUBJECT]}, pluck="name"
        ):
            frappe.delete_doc("HD Ticket", ticket, force=True)
        for account in frappe.get_all("Email Account", pluck="name"):
            frappe.delete_doc("Email Account", account, force=True)

    def setup_complete(self) -> int:
        return frappe.db.get_single_value("HD Settings", "setup_complete")

    def test_a_site_with_only_the_welcome_ticket_stays_pending(self) -> None:
        execute()

        self.assertEqual(self.setup_complete(), 0)

    def test_a_site_with_a_real_ticket_is_marked_complete(self) -> None:
        make_ticket(subject="A real customer question")

        execute()

        self.assertEqual(self.setup_complete(), 1)

    def test_a_site_with_an_email_account_is_marked_complete(self) -> None:
        make_email_account(enable_incoming=0)

        execute()

        self.assertEqual(self.setup_complete(), 1)
