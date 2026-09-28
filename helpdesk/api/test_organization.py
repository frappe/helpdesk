# Copyright (c) 2025, Frappe Technologies and Contributors
# See license.txt

import frappe
from frappe.core.api.user_invitation import get_pending_invitations
from frappe.tests import IntegrationTestCase

from helpdesk.api.organization import (
    get_invitable_contacts,
    invite_members,
    update_member_role,
)
from helpdesk.test_utils import (
    create_agent,
    create_contact,
    create_customer,
    delete_invitations,
    get_invitable_emails,
    get_organization_card,
    get_organization_members,
    make_ticket,
)
from helpdesk.utils import CUSTOMER_PORTAL_ROOT

NEWCOMER = "newcomer@invitations.test"


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
        self.addCleanup(frappe.set_user, "Administrator")

    def members(self) -> dict:
        return get_organization_members(self.customer.name)

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
        self.assertEqual(members[self.owner["contact"]]["role"], "Owner")
        self.assertEqual(members[self.manager["contact"]]["role"], "Manager")
        self.assertEqual(members[self.member["contact"]]["role"], "Member")

    def test_the_caller_is_marked_as_you(self) -> None:
        you = [m for m in self.members().values() if m["is_you"]]
        self.assertEqual(
            [member["contact"] for member in you], [self.manager["contact"]]
        )

    def test_a_manager_can_switch_a_member_to_manager(self) -> None:
        update_member_role(self.customer.name, self.member["contact"], True)
        self.assertEqual(self.is_manager(self.member["contact"]), 1)
        self.assertEqual(self.members()[self.member["contact"]]["role"], "Manager")

        update_member_role(self.customer.name, self.member["contact"], False)
        self.assertEqual(self.is_manager(self.member["contact"]), 0)

    def is_manager(self, contact: str) -> int:
        return frappe.db.get_value(
            "HD Customer Member",
            {"parent": self.customer.name, "contact_name": contact},
            "is_manager",
        )

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


class TestInvitations(IntegrationTestCase):
    """A customer manager invites into the organization they manage and sees no other."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        frappe.set_user("Administrator")
        cls.manager = create_contact("Invite Sender", "sender@invitations.test")
        cls.customer = create_customer(
            "Test Invitations",
            [{"contact_name": cls.manager["contact"], "is_manager": 1}],
        )
        cls.other_customer = create_customer("Test Other Invitations")
        frappe.db.set_single_value(
            "HD Settings", "allow_customer_managers_to_invite", 1
        )

    def setUp(self) -> None:
        frappe.set_user(self.manager["user"])
        self.addCleanup(frappe.set_user, "Administrator")
        self.addCleanup(delete_invitations, NEWCOMER)

    def test_an_invitation_lands_in_the_managed_organization(self) -> None:
        invite_members(self.customer.name, [NEWCOMER], "HD Customer")

        invitation = frappe.db.get_value(
            "User Invitation",
            {"email": NEWCOMER},
            ["name", "status", "customer", "redirect_to_path"],
            as_dict=True,
        )
        self.assertEqual(invitation.status, "Pending")
        self.assertEqual(invitation.customer, self.customer.name)
        self.assertEqual(invitation.redirect_to_path, CUSTOMER_PORTAL_ROOT)
        roles = frappe.get_all("User Role", {"parent": invitation.name}, pluck="role")
        self.assertEqual(roles, ["HD Customer"])

    def test_a_manager_cannot_invite_into_another_organization(self) -> None:
        with self.assertRaises(frappe.PermissionError):
            invite_members(self.other_customer.name, [NEWCOMER], "HD Customer")

    def test_the_invitation_itself_refuses_another_organization(self) -> None:
        with self.assertRaises(frappe.ValidationError):
            frappe.get_doc(
                doctype="User Invitation",
                email=NEWCOMER,
                roles=[{"role": "HD Customer"}],
                app_name="helpdesk",
                redirect_to_path=CUSTOMER_PORTAL_ROOT,
                customer=self.other_customer.name,
            ).insert(ignore_permissions=True)

    def test_a_manager_cannot_list_the_helpdesk_invitations(self) -> None:
        with self.assertRaises(frappe.PermissionError):
            get_pending_invitations("helpdesk")

    def test_invites_need_the_portal_setting(self) -> None:
        frappe.db.set_single_value(
            "HD Settings", "allow_customer_managers_to_invite", 0
        )
        self.addCleanup(
            frappe.db.set_single_value,
            "HD Settings",
            "allow_customer_managers_to_invite",
            1,
        )
        with self.assertRaises(frappe.PermissionError):
            invite_members(self.customer.name, [NEWCOMER], "HD Customer")


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
        cls.customer.db_set("domain", "invitable.test")
        frappe.db.set_single_value(
            "HD Settings", "allow_customer_managers_to_invite", 1
        )

    def setUp(self) -> None:
        frappe.set_user(self.manager["user"])
        self.addCleanup(frappe.set_user, "Administrator")

    def emails(self) -> list[str]:
        return get_invitable_emails(self.customer.name)

    def test_a_contact_with_a_user_is_suggested(self) -> None:
        self.assertIn("colleague@invitable.test", self.emails())

    def test_contacts_off_the_email_domain_are_not_suggested(self) -> None:
        self.assertNotIn("outsider@elsewhere.test", self.emails())

    def test_an_organization_without_a_domain_suggests_nobody(self) -> None:
        self.customer.db_set("domain", None)
        self.addCleanup(self.customer.db_set, "domain", "invitable.test")
        self.assertEqual(self.emails(), [])

    def test_existing_members_are_not_suggested(self) -> None:
        self.assertNotIn("manager@invitable.test", self.emails())

    def test_a_pending_invitee_is_not_suggested(self) -> None:
        invite_members(self.customer.name, ["colleague@invitable.test"], "HD Customer")
        self.addCleanup(delete_invitations, "colleague@invitable.test")
        self.assertNotIn("colleague@invitable.test", self.emails())

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
        self.addCleanup(frappe.set_user, "Administrator")

    def card(self) -> dict:
        return get_organization_card(self.customer.name)

    def test_the_ticket_count_includes_settled_tickets(self) -> None:
        self.assertEqual(self.card()["ticket_count"], 2)

    def test_members_are_counted(self) -> None:
        self.assertEqual(self.card()["member_count"], 1)
