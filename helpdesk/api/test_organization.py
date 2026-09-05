# Copyright (c) 2025, Frappe Technologies and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.api.organization import (
    get_invitable_contacts,
    get_organization,
    get_organizations,
    update_member_role,
)
from helpdesk.test_utils import (
    create_agent,
    create_contact,
    create_customer,
    make_ticket,
)


class TestOrganizationMembers(IntegrationTestCase):
    """The payload behind the portal's member list, and the guards on changing it."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        frappe.set_user("Administrator")
        cls.owner = create_contact("Org Owner", "org-owner@example.com")
        cls.manager = create_contact("Org Manager", "org-manager@example.com")
        cls.member = create_contact("Org Member", "org-member@example.com")
        cls.customer = create_customer(
            "Test Member List",
            [
                {"contact_name": cls.owner["contact"]},
                {"contact_name": cls.manager["contact"], "is_manager": 1},
                {"contact_name": cls.member["contact"]},
            ],
        )
        cls.customer.primary_contact = cls.owner["contact"]
        cls.customer.save()
        # `update_member_role` is gated on this being on. Set here rather than left to
        # whatever the site happens to carry, so these pass on a fresh site too.
        frappe.db.set_single_value(
            "HD Settings", "allow_customer_managers_to_invite", 1
        )

    def setUp(self) -> None:
        frappe.set_user(self.manager["user"])

    def tearDown(self) -> None:
        frappe.set_user("Administrator")

    def members(self) -> dict:
        return {
            member["contact"]: member
            for member in get_organization(self.customer.name)["members"]
        }

    def test_last_seen_comes_from_the_linked_user(self) -> None:
        stamp = "2026-08-01 09:30:00"
        frappe.db.set_value("User", self.member["user"], "last_active", stamp)
        member = self.members()[self.member["contact"]]
        self.assertEqual(str(member["last_seen"]), stamp)

    def test_a_member_who_never_signed_in_has_no_last_seen(self) -> None:
        frappe.db.set_value("User", self.member["user"], "last_active", None)
        self.assertIsNone(self.members()[self.member["contact"]]["last_seen"])

    def test_roles_describe_the_membership(self) -> None:
        members = self.members()
        self.assertTrue(members[self.owner["contact"]]["is_owner"])
        self.assertTrue(members[self.manager["contact"]]["is_manager"])
        self.assertFalse(members[self.member["contact"]]["is_manager"])

    def test_the_caller_is_marked_as_you(self) -> None:
        you = [m for m in self.members().values() if m["is_you"]]
        self.assertEqual(
            [member["contact"] for member in you], [self.manager["contact"]]
        )

    def test_a_manager_can_switch_a_member_to_manager(self) -> None:
        update_member_role(self.customer.name, self.member["contact"], True)
        self.assertTrue(self.members()[self.member["contact"]]["is_manager"])

        update_member_role(self.customer.name, self.member["contact"], False)
        self.assertFalse(self.members()[self.member["contact"]]["is_manager"])

    def test_the_owner_role_cannot_be_switched(self) -> None:
        with self.assertRaises(frappe.ValidationError):
            update_member_role(self.customer.name, self.owner["contact"], False)

    def test_you_cannot_switch_your_own_role(self) -> None:
        with self.assertRaises(frappe.ValidationError):
            update_member_role(self.customer.name, self.manager["contact"], False)

    def test_a_plain_member_cannot_switch_anyone(self) -> None:
        frappe.set_user(self.member["user"])
        with self.assertRaises(frappe.PermissionError):
            update_member_role(self.customer.name, self.manager["contact"], False)


class TestInvitableContacts(IntegrationTestCase):
    """Suggestions for the invite screen, and the line they must not cross."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        frappe.set_user("Administrator")
        cls.manager = create_contact("Invite Manager", "manager@invitable.test")
        cls.colleague = create_contact("Invite Colleague", "colleague@invitable.test")
        cls.outsider = create_contact("Invite Outsider", "outsider@elsewhere.test")
        cls.agent = create_contact("Invite Agent", "agent@invitable.test")
        create_agent("agent@invitable.test")
        cls.customer = create_customer(
            "Test Invitable",
            [{"contact_name": cls.manager["contact"], "is_manager": 1}],
        )

    def setUp(self) -> None:
        frappe.set_user(self.manager["user"])

    def tearDown(self) -> None:
        frappe.set_user("Administrator")

    def emails(self) -> list[str]:
        return [row["email"] for row in get_invitable_contacts(self.customer.name)]

    def test_a_contact_with_a_user_is_suggested(self) -> None:
        self.assertIn("colleague@invitable.test", self.emails())

    def test_the_email_domain_does_not_narrow_the_list(self) -> None:
        self.assertIn("outsider@elsewhere.test", self.emails())

    def test_existing_members_are_not_suggested(self) -> None:
        self.assertNotIn("manager@invitable.test", self.emails())

    def test_agents_are_not_suggested(self) -> None:
        self.assertNotIn("agent@invitable.test", self.emails())

    def test_a_non_manager_cannot_read_the_suggestions(self) -> None:
        frappe.set_user(self.colleague["user"])
        with self.assertRaises(frappe.PermissionError):
            get_invitable_contacts(self.customer.name)


class TestOrganizationCards(IntegrationTestCase):
    """The counts each organization card carries."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        frappe.set_user("Administrator")
        cls.member = create_contact("Card Member", "member@cards.test")
        cls.customer = create_customer(
            "Test Org Cards", [{"contact_name": cls.member["contact"]}]
        )
        for status in ("Open", "Closed"):
            ticket = make_ticket(
                subject=f"{status} card ticket",
                raised_by=cls.member["user"],
                customer=cls.customer.name,
            )
            ticket.db_set("status", status, update_modified=False)
            ticket.db_set("customer", cls.customer.name, update_modified=False)

    def setUp(self) -> None:
        frappe.set_user(self.member["user"])

    def tearDown(self) -> None:
        frappe.set_user("Administrator")

    def card(self) -> dict:
        return next(
            org for org in get_organizations() if org["name"] == self.customer.name
        )

    def test_the_ticket_count_includes_settled_tickets(self) -> None:
        # Was open-only, which read as "nothing on file" for an organization whose
        # tickets had all been answered.
        self.assertEqual(self.card()["ticket_count"], 2)

    def test_members_are_counted(self) -> None:
        self.assertEqual(self.card()["member_count"], 1)
