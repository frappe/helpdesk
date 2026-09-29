from unittest.mock import MagicMock, patch

import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.api.customer_portal_notice import (
    NOTICE_FLAG,
    dismiss_notice,
    promote_all_contacts_to_managers,
    restore_ticket_access,
)
from helpdesk.test_utils import create_agent, create_contact, create_customer


def unique_email(prefix: str) -> str:
    return f"{prefix}-{frappe.generate_hash(length=6)}@example.com"


def make_agent_manager() -> str:
    email = create_agent(unique_email("notice-manager")).name
    frappe.get_doc("User", email).add_roles("Agent Manager")
    return email


def notice_is_shown() -> bool:
    return bool(frappe.db.get_single_value("HD Settings", NOTICE_FLAG))


def roles_of(user: str) -> list[str]:
    return frappe.get_all(
        "Has Role", filters={"parent": user, "parenttype": "User"}, pluck="role"
    )


class TestDismissNotice(IntegrationTestCase):
    def setUp(self) -> None:
        frappe.set_user("Administrator")

    def test_administrator_dismisses_notice_and_notifies_clients(self) -> None:
        with self.change_settings("HD Settings", {NOTICE_FLAG: 1}):
            publish_realtime = self.dismiss_as("Administrator")
            self.assertFalse(notice_is_shown())

        publish_realtime.assert_called_once()
        event = publish_realtime.call_args.args[0]
        self.assertEqual(event, "helpdesk:settings-updated")

    def test_agent_manager_dismisses_notice(self) -> None:
        manager = make_agent_manager()
        with self.change_settings("HD Settings", {NOTICE_FLAG: 1}):
            self.dismiss_as(manager)
            self.assertFalse(notice_is_shown())

    def test_agent_cannot_dismiss_notice(self) -> None:
        agent = create_agent(unique_email("notice-agent")).name
        with self.change_settings("HD Settings", {NOTICE_FLAG: 1}):
            with self.assertRaises(frappe.PermissionError):
                self.dismiss_as(agent)
            self.assertTrue(notice_is_shown())

    def test_customer_cannot_dismiss_notice(self) -> None:
        customer = create_contact("Notice Customer", unique_email("notice-customer"))
        with self.change_settings("HD Settings", {NOTICE_FLAG: 1}):
            with self.assertRaises(frappe.PermissionError):
                self.dismiss_as(customer["user"])
            self.assertTrue(notice_is_shown())

    def dismiss_as(self, user: str) -> MagicMock:
        """Dismiss the notice as `user`, returning the realtime publisher mock."""
        with patch("frappe.publish_realtime") as publish_realtime, self.set_user(user):
            dismiss_notice()
        return publish_realtime


class TestRestoreTicketAccess(IntegrationTestCase):
    def setUp(self) -> None:
        frappe.set_user("Administrator")

    def test_administrator_queues_promotion_and_dismisses_notice(self) -> None:
        with self.change_settings("HD Settings", {NOTICE_FLAG: 1}):
            enqueue = self.restore_as("Administrator")
            self.assertFalse(notice_is_shown())

        enqueue.assert_called_once()
        self.assertIs(enqueue.call_args.args[0], promote_all_contacts_to_managers)
        self.assertTrue(enqueue.call_args.kwargs["deduplicate"])

    def test_agent_manager_queues_promotion(self) -> None:
        self.restore_as(make_agent_manager()).assert_called_once()

    def test_agent_cannot_restore_access(self) -> None:
        agent = create_agent(unique_email("restore-agent")).name
        with self.change_settings("HD Settings", {NOTICE_FLAG: 1}):
            with self.assertRaises(frappe.PermissionError):
                self.restore_as(agent)
            self.assertTrue(notice_is_shown())

    def test_customer_cannot_restore_access(self) -> None:
        customer = create_contact("Restore Customer", unique_email("restore-customer"))
        with self.assertRaises(frappe.PermissionError):
            self.restore_as(customer["user"])

    def restore_as(self, user: str) -> MagicMock:
        """Restore access as `user`, returning the enqueue mock."""
        with patch("frappe.enqueue") as enqueue, self.set_user(user):
            restore_ticket_access()
        return enqueue


class TestPromoteAllContactsToManagers(IntegrationTestCase):
    def setUp(self) -> None:
        frappe.set_user("Administrator")
        self.member = create_contact("Plain Member", unique_email("plain-member"))
        self.manager = create_contact("Manager", unique_email("already-manager"))
        self.no_user = create_contact("No User", unique_email("no-user"), user=False)
        self.customer = create_customer(
            f"Notice Customer {frappe.generate_hash(length=6)}",
            [
                {"contact_name": self.member["contact"]},
                {"contact_name": self.manager["contact"], "is_manager": 1},
                {"contact_name": self.no_user["contact"]},
            ],
        )

    def test_every_member_becomes_manager_with_both_roles(self) -> None:
        promote_all_contacts_to_managers()

        self.customer.reload()
        self.assertTrue(all(row.is_manager for row in self.customer.contacts))
        for user in (self.member["user"], self.manager["user"]):
            with self.subTest(user=user):
                self.assertIn("HD Customer Manager", roles_of(user))
                self.assertIn("HD Customer", roles_of(user))

    def test_running_twice_does_not_duplicate_roles(self) -> None:
        promote_all_contacts_to_managers()
        promote_all_contacts_to_managers()

        roles = roles_of(self.member["user"])
        self.assertEqual(roles.count("HD Customer Manager"), 1)
        self.assertEqual(roles.count("HD Customer"), 1)
