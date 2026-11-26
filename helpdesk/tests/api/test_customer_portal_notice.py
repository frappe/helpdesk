from unittest.mock import MagicMock, patch

import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.api.customer_portal_notice import (
    promote_all_contacts_to_managers,
    restore_ticket_access,
)
from helpdesk.test_utils import (
    create_agent,
    create_contact,
    create_customer,
    get_user_roles,
    make_agent_manager,
    unique_email,
)


class TestRestoreTicketAccess(IntegrationTestCase):
    def setUp(self) -> None:
        frappe.set_user("Administrator")

    def test_administrator_queues_promotion(self) -> None:
        enqueue = self.restore_as("Administrator")

        enqueue.assert_called_once()
        self.assertIs(enqueue.call_args.args[0], promote_all_contacts_to_managers)
        self.assertTrue(enqueue.call_args.kwargs["deduplicate"])

    def test_agent_manager_queues_promotion(self) -> None:
        self.restore_as(make_agent_manager("notice-manager")).assert_called_once()

    def test_agent_cannot_restore_access(self) -> None:
        agent = create_agent(unique_email("restore-agent")).name
        with self.assertRaises(frappe.PermissionError):
            self.restore_as(agent)

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
                self.assertIn("HD Customer Manager", get_user_roles(user))
                self.assertIn("HD Customer", get_user_roles(user))

    def test_running_twice_does_not_duplicate_roles(self) -> None:
        promote_all_contacts_to_managers()
        promote_all_contacts_to_managers()

        roles = get_user_roles(self.member["user"])
        self.assertEqual(roles.count("HD Customer Manager"), 1)
        self.assertEqual(roles.count("HD Customer"), 1)
