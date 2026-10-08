# Copyright (c) 2025, Frappe Technologies and Contributors
# See license.txt

import frappe
from frappe.core.api.user_invitation import get_pending_invitations
from frappe.tests import IntegrationTestCase

from helpdesk.api.organization import (
    MAX_INVITES,
    cancel_invitation,
    get_invitable_contacts,
    get_organization,
    invite_members,
    remove_member,
    update_member_role,
    update_organization_image,
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
    set_setting_for_test_class,
)
from helpdesk.utils import CUSTOMER_PORTAL_ROOT

NEWCOMER = "newcomer@invitations.test"
INVITEE = "invitee@invitations.test"


class TestOrganizationMembers(IntegrationTestCase):
    """The payload behind the portal's member list, and the guards on changing it."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        frappe.set_user("Administrator")
        cls.owner = create_contact("Org Owner", "org-owner@example.com")
        cls.manager = create_contact("Org Manager", "org-manager@example.com")
        cls.member = create_contact("Org Member", "org-member@example.com")
        cls.outsider = create_contact("Org Outsider", "org-outsider@example.com")
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
        # `update_member_role` needs this on; set here so a fresh site passes too.
        set_setting_for_test_class(cls, "allow_customer_managers_to_change_roles", 1)

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

    def test_a_non_member_cannot_read_the_organization(self) -> None:
        frappe.set_user(self.outsider["user"])
        with self.assertRaises(frappe.PermissionError):
            get_organization(self.customer.name)

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

    def test_role_changes_need_their_own_portal_setting(self) -> None:
        self.addCleanup(
            frappe.db.set_single_value,
            "HD Settings",
            "allow_customer_managers_to_invite",
            frappe.db.get_single_value(
                "HD Settings", "allow_customer_managers_to_invite"
            ),
        )
        frappe.db.set_single_value(
            "HD Settings", "allow_customer_managers_to_invite", 1
        )
        frappe.db.set_single_value(
            "HD Settings", "allow_customer_managers_to_change_roles", 0
        )
        self.addCleanup(
            frappe.db.set_single_value,
            "HD Settings",
            "allow_customer_managers_to_change_roles",
            1,
        )
        with self.assertRaises(frappe.PermissionError):
            update_member_role(self.customer.name, self.member["contact"], True)

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
        set_setting_for_test_class(cls, "allow_customer_managers_to_invite", 1)

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

    def test_an_invitation_is_listed_apart_from_the_members(self) -> None:
        invite_members(self.customer.name, [NEWCOMER], "HD Customer")

        organization = get_organization(self.customer.name)

        self.assertEqual([row["email"] for row in organization["invites"]], [NEWCOMER])
        self.assertNotIn(NEWCOMER, [row["email"] for row in organization["members"]])

    def test_invitations_are_hidden_once_inviting_is_off(self) -> None:
        invite_members(self.customer.name, [NEWCOMER], "HD Customer")
        frappe.db.set_single_value(
            "HD Settings", "allow_customer_managers_to_invite", 0
        )
        self.addCleanup(
            frappe.db.set_single_value,
            "HD Settings",
            "allow_customer_managers_to_invite",
            1,
        )

        self.assertEqual(get_organization(self.customer.name)["invites"], [])

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

    def test_a_role_outside_the_customer_roles_is_refused(self) -> None:
        with self.assertRaises(frappe.ValidationError):
            invite_members(self.customer.name, [NEWCOMER], "System Manager")

    def test_a_refused_email_stops_the_whole_batch(self) -> None:
        invite_members(self.customer.name, [INVITEE], "HD Customer")
        self.addCleanup(delete_invitations, INVITEE)

        with self.assertRaises(frappe.ValidationError):
            invite_members(self.customer.name, [NEWCOMER, INVITEE], "HD Customer")

        self.assertFalse(frappe.db.exists("User Invitation", {"email": NEWCOMER}))

    def test_a_repeated_email_is_invited_once(self) -> None:
        invite_members(self.customer.name, [NEWCOMER, NEWCOMER], "HD Customer")
        self.assertEqual(frappe.db.count("User Invitation", {"email": NEWCOMER}), 1)

    def test_more_than_the_cap_is_refused(self) -> None:
        emails = [f"invitee{i}@invitations.test" for i in range(MAX_INVITES + 1)]
        with self.assertRaises(frappe.ValidationError):
            invite_members(self.customer.name, emails, "HD Customer")


class TestMemberRemoval(IntegrationTestCase):
    """Who a manager may drop, and whose invitations they may cancel."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        frappe.set_user("Administrator")
        cls.owner = create_contact("Removal Owner", "owner@removal.test")
        cls.manager = create_contact("Removal Manager", "manager@removal.test")
        cls.member = create_contact("Removal Member", "member@removal.test")
        cls.customer = create_customer(
            "Test Member Removal",
            [
                {"contact_name": cls.owner["contact"]},
                {"contact_name": cls.manager["contact"], "is_manager": 1},
                {"contact_name": cls.member["contact"]},
            ],
        )
        cls.customer.primary_contact = cls.owner["contact"]
        cls.customer.save()
        cls.other_customer = create_customer("Test Other Removal")
        # Removing needs its own setting; cancelling an invitation needs the invite one.
        set_setting_for_test_class(cls, "allow_customer_managers_to_invite", 1)
        set_setting_for_test_class(cls, "allow_customer_managers_to_remove_members", 1)

    def setUp(self) -> None:
        frappe.set_user(self.manager["user"])
        self.addCleanup(frappe.set_user, "Administrator")

    def member_contacts(self) -> list[str]:
        customer = frappe.get_doc("HD Customer", self.customer.name)
        return [row.contact_name for row in customer.contacts]

    def readd_member(self) -> None:
        frappe.set_user("Administrator")
        customer = frappe.get_doc("HD Customer", self.customer.name)
        customer.append("contacts", {"contact_name": self.member["contact"]})
        customer.save()

    def test_a_manager_removes_a_member(self) -> None:
        remove_member(self.customer.name, self.member["contact"])
        self.addCleanup(self.readd_member)

        self.assertNotIn(self.member["contact"], self.member_contacts())

    def test_the_owner_cannot_be_removed(self) -> None:
        with self.assertRaises(frappe.ValidationError):
            remove_member(self.customer.name, self.owner["contact"])

    def test_you_cannot_remove_yourself(self) -> None:
        with self.assertRaises(frappe.ValidationError):
            remove_member(self.customer.name, self.manager["contact"])

    def test_a_plain_member_cannot_remove_anyone(self) -> None:
        frappe.set_user(self.member["user"])
        with self.assertRaises(frappe.PermissionError):
            remove_member(self.customer.name, self.owner["contact"])

    def test_removal_needs_its_own_portal_setting(self) -> None:
        frappe.db.set_single_value(
            "HD Settings", "allow_customer_managers_to_remove_members", 0
        )
        self.addCleanup(
            frappe.db.set_single_value,
            "HD Settings",
            "allow_customer_managers_to_remove_members",
            1,
        )
        with self.assertRaises(frappe.PermissionError):
            remove_member(self.customer.name, self.member["contact"])

    def test_a_manager_cancels_an_invitation(self) -> None:
        invite_members(self.customer.name, [NEWCOMER], "HD Customer")
        self.addCleanup(delete_invitations, NEWCOMER)
        invitation = frappe.db.get_value("User Invitation", {"email": NEWCOMER})

        cancel_invitation(self.customer.name, invitation)

        status = frappe.db.get_value("User Invitation", invitation, "status")
        self.assertEqual(status, "Cancelled")

    def test_another_organizations_invitation_is_refused(self) -> None:
        frappe.set_user("Administrator")
        invitation = frappe.get_doc(
            doctype="User Invitation",
            email=NEWCOMER,
            roles=[{"role": "HD Customer"}],
            app_name="helpdesk",
            redirect_to_path=CUSTOMER_PORTAL_ROOT,
            customer=self.other_customer.name,
        ).insert()
        self.addCleanup(delete_invitations, NEWCOMER)
        frappe.set_user(self.manager["user"])

        with self.assertRaises(frappe.PermissionError):
            cancel_invitation(self.customer.name, invitation.name)


class TestOrganizationEdits(IntegrationTestCase):
    """Changing the logo, behind its own portal setting."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        frappe.set_user("Administrator")
        cls.manager = create_contact("Edit Manager", "manager@edits.test")
        cls.member = create_contact("Edit Member", "member@edits.test")
        cls.customer = create_customer(
            "Test Org Edits",
            [
                {"contact_name": cls.manager["contact"], "is_manager": 1},
                {"contact_name": cls.member["contact"]},
            ],
        )
        set_setting_for_test_class(
            cls, "allow_customer_managers_to_edit_organization", 1
        )

    def setUp(self) -> None:
        frappe.set_user(self.manager["user"])
        self.addCleanup(frappe.set_user, "Administrator")

    def test_edits_need_the_portal_setting(self) -> None:
        frappe.db.set_single_value(
            "HD Settings", "allow_customer_managers_to_edit_organization", 0
        )
        self.addCleanup(
            frappe.db.set_single_value,
            "HD Settings",
            "allow_customer_managers_to_edit_organization",
            1,
        )
        with self.assertRaises(frappe.PermissionError):
            update_organization_image(self.customer.name, "/files/logo.png")

    def test_a_plain_member_cannot_edit(self) -> None:
        frappe.set_user(self.member["user"])
        with self.assertRaises(frappe.PermissionError):
            update_organization_image(self.customer.name, "/files/logo.png")

    def test_a_linked_logo_is_refused(self) -> None:
        with self.assertRaises(frappe.ValidationError):
            update_organization_image(self.customer.name, "https://tracker.test/a.png")

    def test_a_manager_can_set_and_clear_the_logo(self) -> None:
        update_organization_image(self.customer.name, "/files/logo.png")
        self.assertEqual(
            frappe.db.get_value("HD Customer", self.customer.name, "image"),
            "/files/logo.png",
        )
        update_organization_image(self.customer.name, "")
        self.assertIsNone(
            frappe.db.get_value("HD Customer", self.customer.name, "image")
        )

    def test_the_creator_s_email_is_not_shown_as_the_organization_s(self) -> None:
        self.assertIsNone(get_organization(self.customer.name)["email"])


class TestInvitableContacts(IntegrationTestCase):
    """Suggestions for the invite screen, and the line they must not cross."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        frappe.set_user("Administrator")
        cls.manager = create_contact("Invite Manager", "manager@invitable.test")
        cls.colleague = create_contact("Invite Colleague", "colleague@invitable.test")
        cls.outsider = create_contact("Invite Outsider", "outsider@elsewhere.test")
        cls.stranger = create_contact("Invite Stranger", "stranger@gmail.com")
        cls.agent = create_contact("Invite Agent", "agent@invitable.test")
        create_agent("agent@invitable.test")
        cls.customer = create_customer(
            "Test Invitable",
            [{"contact_name": cls.manager["contact"], "is_manager": 1}],
        )
        cls.customer.db_set("domain", "invitable.test")
        set_setting_for_test_class(cls, "allow_customer_managers_to_invite", 1)

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

    def test_an_organization_on_a_shared_mail_provider_suggests_nobody(self) -> None:
        self.customer.db_set("domain", "Gmail.com")
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
