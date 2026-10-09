# Copyright (c) 2025, Frappe Technologies and Contributors
# See license.txt

import frappe
from frappe.core.api.user_invitation import get_pending_invitations
from frappe.tests import IntegrationTestCase
from frappe.tests.utils import change_settings

from helpdesk.api.organization import (
    MAX_INVITES,
    get_invitable_contacts,
    get_organization,
    invite_members,
    remove_member,
    update_member_role,
    update_organization,
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
    unique_email,
    unique_name,
)
from helpdesk.utils import CUSTOMER_PORTAL_ROOT


class TestOrganizationMembers(IntegrationTestCase):
    """The payload behind the portal's member list, and the guards on changing it."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        frappe.set_user("Administrator")
        cls.owner = create_contact("Org Owner", unique_email("org-owner"))
        cls.manager = create_contact("Org Manager", unique_email("org-manager"))
        cls.member = create_contact("Org Member", unique_email("org-member"))
        cls.outsider = create_contact("Org Outsider", unique_email("org-outsider"))
        cls.customer = create_customer(
            unique_name("Test Member List"),
            [
                {"contact_name": cls.owner["contact"]},
                {"contact_name": cls.manager["contact"], "is_manager": 1},
                {"contact_name": cls.member["contact"]},
            ],
        )
        cls.customer.primary_contact = cls.owner["contact"]
        cls.customer.save()
        cls.enterClassContext(
            change_settings(
                "HD Settings", {"allow_customer_managers_to_change_roles": 1}
            )
        )

    def members(self) -> dict:
        with self.set_user(self.manager["user"]):
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
        with (
            self.set_user(self.outsider["user"]),
            self.assertRaises(frappe.PermissionError),
        ):
            get_organization(self.customer.name)

    def test_a_manager_can_switch_a_member_to_manager(self) -> None:
        with self.set_user(self.manager["user"]):
            update_member_role(self.customer.name, self.member["contact"], True)
        self.assertEqual(self.is_manager(self.member["contact"]), 1)
        self.assertEqual(self.members()[self.member["contact"]]["role"], "Manager")

        with self.set_user(self.manager["user"]):
            update_member_role(self.customer.name, self.member["contact"], False)
        self.assertEqual(self.is_manager(self.member["contact"]), 0)

    def is_manager(self, contact: str) -> int:
        return frappe.db.get_value(
            "HD Customer Member",
            {"parent": self.customer.name, "contact_name": contact},
            "is_manager",
        )

    def test_the_owner_role_cannot_be_switched(self) -> None:
        with (
            self.set_user(self.manager["user"]),
            self.assertRaises(frappe.ValidationError),
        ):
            update_member_role(self.customer.name, self.owner["contact"], False)

    def test_you_cannot_switch_your_own_role(self) -> None:
        with (
            self.set_user(self.manager["user"]),
            self.assertRaises(frappe.ValidationError),
        ):
            update_member_role(self.customer.name, self.manager["contact"], False)

    def test_role_changes_need_their_own_portal_setting(self) -> None:
        settings = {
            "allow_customer_managers_to_invite": 1,
            "allow_customer_managers_to_change_roles": 0,
        }
        with (
            change_settings("HD Settings", settings),
            self.set_user(self.manager["user"]),
            self.assertRaises(frappe.PermissionError),
        ):
            update_member_role(self.customer.name, self.member["contact"], True)

    def test_a_plain_member_cannot_switch_anyone(self) -> None:
        with (
            self.set_user(self.member["user"]),
            self.assertRaises(frappe.PermissionError),
        ):
            update_member_role(self.customer.name, self.manager["contact"], False)


class TestInvitations(IntegrationTestCase):
    """A customer manager invites into the organization they manage and sees no other."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        frappe.set_user("Administrator")
        cls.manager = create_contact("Invite Sender", unique_email("invite-sender"))
        cls.customer = create_customer(
            unique_name("Test Invitations"),
            [{"contact_name": cls.manager["contact"], "is_manager": 1}],
        )
        cls.other_customer = create_customer(unique_name("Test Other Invitations"))
        cls.enterClassContext(
            change_settings("HD Settings", {"allow_customer_managers_to_invite": 1})
        )

    def setUp(self) -> None:
        self.newcomer = unique_email("newcomer")
        self.addCleanup(delete_invitations, self.newcomer)

    def test_an_invitation_lands_in_the_managed_organization(self) -> None:
        with self.set_user(self.manager["user"]):
            invite_members(self.customer.name, [self.newcomer], "HD Customer")

        invitation = frappe.db.get_value(
            "User Invitation",
            {"email": self.newcomer},
            ["name", "status", "customer", "redirect_to_path"],
            as_dict=True,
        )
        self.assertEqual(invitation.status, "Pending")
        self.assertEqual(invitation.customer, self.customer.name)
        self.assertEqual(invitation.redirect_to_path, CUSTOMER_PORTAL_ROOT)
        roles = frappe.get_all("User Role", {"parent": invitation.name}, pluck="role")
        self.assertEqual(roles, ["HD Customer"])

    def test_an_invitation_is_listed_apart_from_the_members(self) -> None:
        with self.set_user(self.manager["user"]):
            invite_members(self.customer.name, [self.newcomer], "HD Customer")
            organization = get_organization(self.customer.name)

        self.assertEqual(
            [row["email"] for row in organization["invites"]], [self.newcomer]
        )
        self.assertNotIn(
            self.newcomer, [row["email"] for row in organization["members"]]
        )

    def test_invitations_are_hidden_once_inviting_is_off(self) -> None:
        with self.set_user(self.manager["user"]):
            invite_members(self.customer.name, [self.newcomer], "HD Customer")

        with (
            change_settings("HD Settings", {"allow_customer_managers_to_invite": 0}),
            self.set_user(self.manager["user"]),
        ):
            self.assertEqual(get_organization(self.customer.name)["invites"], [])

    def test_a_manager_cannot_invite_into_another_organization(self) -> None:
        with (
            self.set_user(self.manager["user"]),
            self.assertRaises(frappe.PermissionError),
        ):
            invite_members(self.other_customer.name, [self.newcomer], "HD Customer")

    def test_the_invitation_itself_refuses_another_organization(self) -> None:
        with (
            self.set_user(self.manager["user"]),
            self.assertRaises(frappe.ValidationError),
        ):
            frappe.get_doc(
                doctype="User Invitation",
                email=self.newcomer,
                roles=[{"role": "HD Customer"}],
                app_name="helpdesk",
                redirect_to_path=CUSTOMER_PORTAL_ROOT,
                customer=self.other_customer.name,
            ).insert(ignore_permissions=True)

    def test_a_manager_cannot_list_the_helpdesk_invitations(self) -> None:
        with (
            self.set_user(self.manager["user"]),
            self.assertRaises(frappe.PermissionError),
        ):
            get_pending_invitations("helpdesk")

    def test_invites_need_the_portal_setting(self) -> None:
        with (
            change_settings("HD Settings", {"allow_customer_managers_to_invite": 0}),
            self.set_user(self.manager["user"]),
            self.assertRaises(frappe.PermissionError),
        ):
            invite_members(self.customer.name, [self.newcomer], "HD Customer")

    def test_a_role_outside_the_customer_roles_is_refused(self) -> None:
        with (
            self.set_user(self.manager["user"]),
            self.assertRaises(frappe.ValidationError),
        ):
            invite_members(self.customer.name, [self.newcomer], "System Manager")

    def test_a_refused_email_stops_the_whole_batch(self) -> None:
        invitee = unique_email("invitee")
        self.addCleanup(delete_invitations, invitee)
        with self.set_user(self.manager["user"]):
            invite_members(self.customer.name, [invitee], "HD Customer")
            with self.assertRaises(frappe.ValidationError):
                invite_members(
                    self.customer.name, [self.newcomer, invitee], "HD Customer"
                )

        self.assertFalse(frappe.db.exists("User Invitation", {"email": self.newcomer}))

    def test_a_repeated_email_is_invited_once(self) -> None:
        with self.set_user(self.manager["user"]):
            invite_members(
                self.customer.name, [self.newcomer, self.newcomer], "HD Customer"
            )
        self.assertEqual(
            frappe.db.count("User Invitation", {"email": self.newcomer}), 1
        )

    def test_more_than_the_cap_is_refused(self) -> None:
        emails = [unique_email("invitee") for _ in range(MAX_INVITES + 1)]
        with (
            self.set_user(self.manager["user"]),
            self.assertRaises(frappe.ValidationError),
        ):
            invite_members(self.customer.name, emails, "HD Customer")


class TestMemberRemoval(IntegrationTestCase):
    """Who a manager may drop, and whose invitations they may cancel."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        frappe.set_user("Administrator")
        cls.owner = create_contact("Removal Owner", unique_email("removal-owner"))
        cls.manager = create_contact("Removal Manager", unique_email("removal-manager"))
        cls.member = create_contact("Removal Member", unique_email("removal-member"))
        cls.customer = create_customer(
            unique_name("Test Member Removal"),
            [
                {"contact_name": cls.owner["contact"]},
                {"contact_name": cls.manager["contact"], "is_manager": 1},
                {"contact_name": cls.member["contact"]},
            ],
        )
        cls.customer.primary_contact = cls.owner["contact"]
        cls.customer.save()
        cls.other_customer = create_customer(unique_name("Test Other Removal"))
        # Removing needs its own setting; cancelling an invitation needs the invite one.
        cls.enterClassContext(
            change_settings(
                "HD Settings",
                {
                    "allow_customer_managers_to_invite": 1,
                    "allow_customer_managers_to_remove_members": 1,
                },
            )
        )

    def member_contacts(self) -> list[str]:
        customer = frappe.get_doc("HD Customer", self.customer.name)
        return [row.contact_name for row in customer.contacts]

    def readd_member(self) -> None:
        customer = frappe.get_doc("HD Customer", self.customer.name)
        customer.append("contacts", {"contact_name": self.member["contact"]})
        customer.save()

    def test_a_manager_removes_a_member(self) -> None:
        with self.set_user(self.manager["user"]):
            remove_member(self.customer.name, self.member["contact"])
        self.addCleanup(self.readd_member)

        self.assertNotIn(self.member["contact"], self.member_contacts())

    def test_the_owner_cannot_be_removed(self) -> None:
        with (
            self.set_user(self.manager["user"]),
            self.assertRaises(frappe.ValidationError),
        ):
            remove_member(self.customer.name, self.owner["contact"])

    def test_you_cannot_remove_yourself(self) -> None:
        with (
            self.set_user(self.manager["user"]),
            self.assertRaises(frappe.ValidationError),
        ):
            remove_member(self.customer.name, self.manager["contact"])

    def test_a_plain_member_cannot_remove_anyone(self) -> None:
        with (
            self.set_user(self.member["user"]),
            self.assertRaises(frappe.PermissionError),
        ):
            remove_member(self.customer.name, self.owner["contact"])

    def test_removal_needs_its_own_portal_setting(self) -> None:
        with (
            change_settings(
                "HD Settings", {"allow_customer_managers_to_remove_members": 0}
            ),
            self.set_user(self.manager["user"]),
            self.assertRaises(frappe.PermissionError),
        ):
            remove_member(self.customer.name, self.member["contact"])

    def test_a_manager_cancels_an_invitation(self) -> None:
        newcomer = unique_email("newcomer")
        self.addCleanup(delete_invitations, newcomer)
        with self.set_user(self.manager["user"]):
            invite_members(self.customer.name, [newcomer], "HD Customer")
            invitation = frappe.db.get_value("User Invitation", {"email": newcomer})
            remove_member(self.customer.name, invitation=invitation)

        status = frappe.db.get_value("User Invitation", invitation, "status")
        self.assertEqual(status, "Cancelled")

    def test_another_organizations_invitation_is_refused(self) -> None:
        newcomer = unique_email("newcomer")
        invitation = frappe.get_doc(
            doctype="User Invitation",
            email=newcomer,
            roles=[{"role": "HD Customer"}],
            app_name="helpdesk",
            redirect_to_path=CUSTOMER_PORTAL_ROOT,
            customer=self.other_customer.name,
        ).insert()
        self.addCleanup(delete_invitations, newcomer)

        with (
            self.set_user(self.manager["user"]),
            self.assertRaises(frappe.PermissionError),
        ):
            remove_member(self.customer.name, invitation=invitation.name)


class TestOrganizationEdits(IntegrationTestCase):
    """Renaming and re-logoing, behind their own portal setting."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        frappe.set_user("Administrator")
        cls.manager = create_contact("Edit Manager", unique_email("edit-manager"))
        cls.member = create_contact("Edit Member", unique_email("edit-member"))
        cls.customer = create_customer(
            unique_name("Test Org Edits"),
            [
                {"contact_name": cls.manager["contact"], "is_manager": 1},
                {"contact_name": cls.member["contact"]},
            ],
        )
        cls.enterClassContext(
            change_settings(
                "HD Settings", {"allow_customer_managers_to_edit_organization": 1}
            )
        )

    def test_edits_need_the_portal_setting(self) -> None:
        with (
            change_settings(
                "HD Settings", {"allow_customer_managers_to_edit_organization": 0}
            ),
            self.set_user(self.manager["user"]),
            self.assertRaises(frappe.PermissionError),
        ):
            update_organization(self.customer.name, image="/files/logo.png")

    def test_a_plain_member_cannot_edit(self) -> None:
        with (
            self.set_user(self.member["user"]),
            self.assertRaises(frappe.PermissionError),
        ):
            update_organization(self.customer.name, image="/files/logo.png")

    def test_a_linked_logo_is_refused(self) -> None:
        with (
            self.set_user(self.manager["user"]),
            self.assertRaises(frappe.ValidationError),
        ):
            update_organization(self.customer.name, image="https://tracker.test/a.png")

    def test_a_rename_answers_with_the_new_name(self) -> None:
        new_name = f"{self.customer.name} Renamed"
        with self.set_user(self.manager["user"]):
            renamed = update_organization(self.customer.name, new_name)
        self.addCleanup(self.rename_back, renamed)

        self.assertEqual(renamed, new_name)
        self.assertTrue(frappe.db.exists("HD Customer", renamed))

    def rename_back(self, renamed: str) -> None:
        frappe.rename_doc("HD Customer", renamed, self.customer.name)

    def test_the_creator_s_email_is_not_shown_as_the_organization_s(self) -> None:
        with self.set_user(self.manager["user"]):
            self.assertIsNone(get_organization(self.customer.name)["email"])


class TestInvitableContacts(IntegrationTestCase):
    """Suggestions for the invite screen, and the line they must not cross."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        frappe.set_user("Administrator")
        cls.domain = f"{frappe.generate_hash(length=8)}.test"
        cls.manager = create_contact("Invite Manager", f"manager@{cls.domain}")
        cls.colleague = create_contact("Invite Colleague", f"colleague@{cls.domain}")
        cls.outsider = create_contact("Invite Outsider", unique_email("outsider"))
        cls.agent = create_contact("Invite Agent", f"agent@{cls.domain}")
        create_agent(cls.agent["user"])
        cls.customer = create_customer(
            unique_name("Test Invitable"),
            [{"contact_name": cls.manager["contact"], "is_manager": 1}],
        )
        cls.customer.db_set("domain", cls.domain)
        cls.enterClassContext(
            change_settings("HD Settings", {"allow_customer_managers_to_invite": 1})
        )

    def emails(self) -> list[str]:
        with self.set_user(self.manager["user"]):
            return get_invitable_emails(self.customer.name)

    def test_a_contact_with_a_user_is_suggested(self) -> None:
        self.assertIn(self.colleague["user"], self.emails())

    def test_contacts_off_the_email_domain_are_not_suggested(self) -> None:
        self.assertNotIn(self.outsider["user"], self.emails())

    def test_an_organization_without_a_domain_suggests_nobody(self) -> None:
        self.customer.db_set("domain", None)
        self.addCleanup(self.customer.db_set, "domain", self.domain)
        self.assertEqual(self.emails(), [])

    def test_existing_members_are_not_suggested(self) -> None:
        self.assertNotIn(self.manager["user"], self.emails())

    def test_a_pending_invitee_is_not_suggested(self) -> None:
        with self.set_user(self.manager["user"]):
            invite_members(self.customer.name, [self.colleague["user"]], "HD Customer")
        self.addCleanup(delete_invitations, self.colleague["user"])
        self.assertNotIn(self.colleague["user"], self.emails())

    def test_agents_are_not_suggested(self) -> None:
        self.assertNotIn(self.agent["user"], self.emails())

    def test_a_non_manager_cannot_read_the_suggestions(self) -> None:
        with (
            self.set_user(self.colleague["user"]),
            self.assertRaises(frappe.PermissionError),
        ):
            get_invitable_contacts(self.customer.name)


class TestOrganizationCards(IntegrationTestCase):
    """The counts each organization card carries."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        frappe.set_user("Administrator")
        cls.member = create_contact("Card Member", unique_email("card-member"))
        cls.customer = create_customer(
            unique_name("Test Org Cards"), [{"contact_name": cls.member["contact"]}]
        )
        for status in ("Open", "Closed"):
            ticket = make_ticket(
                subject=f"{status} card ticket",
                raised_by=cls.member["user"],
                customer=cls.customer.name,
            )
            ticket.db_set("status", status, update_modified=False)
            ticket.db_set("customer", cls.customer.name, update_modified=False)

    def card(self) -> dict:
        with self.set_user(self.member["user"]):
            return get_organization_card(self.customer.name)

    def test_the_ticket_count_includes_settled_tickets(self) -> None:
        self.assertEqual(self.card()["ticket_count"], 2)

    def test_members_are_counted(self) -> None:
        self.assertEqual(self.card()["member_count"], 1)
