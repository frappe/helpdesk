# Copyright (c) 2025, Frappe Technologies and Contributors
# See license.txt

from unittest.mock import patch

import frappe
from frappe.core.api.user_invitation import get_pending_invitations, invite_by_email
from frappe.tests import IntegrationTestCase
from frappe.tests.utils import change_settings

from helpdesk.api.customer import (
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
    get_organization_card,
    get_organization_members,
    make_invitation,
    make_organization,
    make_ticket,
    unique_email,
    unique_name,
)
from helpdesk.utils import CUSTOMER_PORTAL_ROOT


class TestOrganizationMembers(IntegrationTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        frappe.set_user("Administrator")
        cls.customer, cls.owner, cls.manager, cls.member = make_organization("Org")
        cls.outsider = create_contact("Org Outsider", unique_email("org-outsider"))
        cls.enterClassContext(
            change_settings(
                "HD Settings", {"allow_customer_managers_to_manage_organization": 1}
            )
        )

    def members(self) -> dict:
        with self.set_user(self.manager["user"]):
            return get_organization_members(self.customer.name)

    def test_last_active_comes_from_the_linked_user(self) -> None:
        stamp = "2026-08-01 09:30:00"
        frappe.db.set_value("User", self.member["user"], "last_active", stamp)
        member = self.members()[self.member["contact"]]
        self.assertEqual(str(member["last_active"]), stamp)

    def test_a_member_who_never_signed_in_has_no_last_active(self) -> None:
        frappe.db.set_value("User", self.member["user"], "last_active", None)
        self.assertIsNone(self.members()[self.member["contact"]]["last_active"])

    def test_a_plain_member_does_not_see_when_colleagues_last_signed_in(self) -> None:
        frappe.db.set_value(
            "User", self.manager["user"], "last_active", "2026-08-01 09:30:00"
        )
        with self.set_user(self.member["user"]):
            members = get_organization_members(self.customer.name)
        self.assertNotIn("last_active", members[self.manager["contact"]])

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

    def test_the_caller_is_listed_first(self) -> None:
        # a Member, who would otherwise sort after the owner and managers
        with self.set_user(self.member["user"]):
            members = get_organization(self.customer.name)["members"]
        self.assertEqual(members[0]["contact"], self.member["contact"])

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

    def test_role_changes_need_the_member_management_setting(self) -> None:
        settings = {
            "allow_customer_managers_to_invite": 1,
            "allow_customer_managers_to_manage_organization": 0,
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
            change_settings(
                "HD Settings",
                {
                    "allow_customer_managers_to_invite": 1,
                    # some tests invite managers
                    "allow_customer_managers_to_manage_organization": 1,
                },
            )
        )

    def setUp(self) -> None:
        self.newcomer = unique_email("newcomer")
        self.addCleanup(delete_invitations, self.newcomer)

    def test_an_invitation_lands_in_the_managed_organization(self) -> None:
        with self.set_user(self.manager["user"]):
            invite_members(self.customer.name, [self.newcomer], False)

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
            invite_members(self.customer.name, [self.newcomer], False)
            organization = get_organization(self.customer.name)

        self.assertEqual(
            [row["email"] for row in organization["invitations"]], [self.newcomer]
        )
        self.assertNotIn(
            self.newcomer, [row["email"] for row in organization["members"]]
        )

    def test_each_invitation_keeps_its_own_role(self) -> None:
        manager_invitee = unique_email("manager-invitee")
        self.addCleanup(delete_invitations, manager_invitee)
        with self.set_user(self.manager["user"]):
            invite_members(self.customer.name, [self.newcomer], False)
            invite_members(self.customer.name, [manager_invitee], True)
            invitations = get_organization(self.customer.name)["invitations"]

        roles = {row["email"]: row["role"] for row in invitations}
        self.assertEqual(roles, {self.newcomer: "Member", manager_invitee: "Manager"})

    def test_invitations_are_hidden_once_inviting_is_off(self) -> None:
        with self.set_user(self.manager["user"]):
            invite_members(self.customer.name, [self.newcomer], False)

        with (
            change_settings("HD Settings", {"allow_customer_managers_to_invite": 0}),
            self.set_user(self.manager["user"]),
        ):
            self.assertEqual(get_organization(self.customer.name)["invitations"], [])

    def test_a_manager_cannot_invite_into_another_organization(self) -> None:
        with (
            self.set_user(self.manager["user"]),
            self.assertRaises(frappe.PermissionError),
        ):
            invite_members(self.other_customer.name, [self.newcomer], False)

    def test_the_invitation_itself_refuses_another_organization(self) -> None:
        with (
            self.set_user(self.manager["user"]),
            self.assertRaises(frappe.ValidationError),
        ):
            make_invitation(self.newcomer, self.other_customer.name)

    def test_a_manager_cannot_list_the_helpdesk_invitations(self) -> None:
        with (
            self.set_user(self.manager["user"]),
            self.assertRaises(frappe.PermissionError),
        ):
            get_pending_invitations("helpdesk")

    def test_a_manager_cannot_use_the_agent_desk_invite_list(self) -> None:
        with (
            self.set_user(self.manager["user"]),
            self.assertRaises(frappe.PermissionError),
        ):
            self.customer.get_pending_invites()

    def test_invitations_need_the_portal_setting(self) -> None:
        with (
            change_settings("HD Settings", {"allow_customer_managers_to_invite": 0}),
            self.set_user(self.manager["user"]),
            self.assertRaises(frappe.PermissionError),
        ):
            invite_members(self.customer.name, [self.newcomer], False)

    def test_inviting_a_manager_needs_the_role_setting(self) -> None:
        with (
            change_settings(
                "HD Settings", {"allow_customer_managers_to_manage_organization": 0}
            ),
            self.set_user(self.manager["user"]),
            self.assertRaises(frappe.PermissionError),
        ):
            invite_members(self.customer.name, [self.newcomer], True)

    def test_an_already_invited_email_is_skipped(self) -> None:
        invitee = unique_email("invitee")
        self.addCleanup(delete_invitations, invitee)
        with self.set_user(self.manager["user"]):
            invite_members(self.customer.name, [invitee], False)
            result = invite_members(self.customer.name, [self.newcomer, invitee], False)

        # no per-email reason: the checks span the whole site
        self.assertEqual(
            result,
            {
                "invited_emails": [self.newcomer],
                "skipped_emails": [invitee],
                "disabled_emails": [],
            },
        )

    def test_a_disabled_user_is_reported_apart(self) -> None:
        email = unique_email("disabled")
        create_contact("Disabled User", email)
        frappe.db.set_value("User", email, "enabled", 0)
        with self.set_user(self.manager["user"]):
            result = invite_members(self.customer.name, [email], False)

        self.assertEqual(
            result,
            {"invited_emails": [], "skipped_emails": [], "disabled_emails": [email]},
        )

    def test_an_existing_member_is_skipped(self) -> None:
        """Accepting would bypass the manage organization setting."""
        email = unique_email("existing-member")
        member = create_contact("Existing Member", email)
        frappe.get_doc("HD Customer", self.customer.name).add_contacts(
            [member["contact"]]
        )
        self.addCleanup(delete_invitations, email)
        with self.set_user(self.manager["user"]):
            result = invite_members(self.customer.name, [email], True)

        self.assertEqual(
            result,
            {"invited_emails": [], "skipped_emails": [email], "disabled_emails": []},
        )

    def test_an_existing_member_is_skipped_in_any_case(self) -> None:
        email = unique_email("cased-member")
        member = create_contact("Cased Member", email)
        frappe.get_doc("HD Customer", self.customer.name).add_contacts(
            [member["contact"]]
        )
        self.addCleanup(delete_invitations, email)
        with self.set_user(self.manager["user"]):
            result = invite_members(self.customer.name, [email.upper()], True)

        self.assertEqual(
            result,
            {"invited_emails": [], "skipped_emails": [email], "disabled_emails": []},
        )

    def test_frappes_invite_endpoint_refuses_a_manager(self) -> None:
        """The `user_invitation` hook also guards Frappe's cancel and resend."""
        with (
            self.set_user(self.manager["user"]),
            self.assertRaises(frappe.PermissionError),
        ):
            invite_by_email(
                self.newcomer,
                roles=["HD Customer"],
                redirect_to_path="/help",
                app_name="helpdesk",
                customer=self.customer.name,
            )

    def test_a_repeated_email_is_invited_once(self) -> None:
        with self.set_user(self.manager["user"]):
            invite_members(self.customer.name, [self.newcomer, self.newcomer], False)
        self.assertEqual(
            frappe.db.count("User Invitation", {"email": self.newcomer}), 1
        )

    def test_more_than_the_cap_is_refused(self) -> None:
        emails = [unique_email("invitee") for _ in range(MAX_INVITES + 1)]
        with (
            self.set_user(self.manager["user"]),
            self.assertRaises(frappe.ValidationError),
        ):
            invite_members(self.customer.name, emails, False)

    def test_more_than_the_hourly_cap_is_refused(self) -> None:
        first, second = unique_email("hourly"), unique_email("hourly")
        self.addCleanup(delete_invitations, first)
        with (
            patch("helpdesk.api.customer.MAX_INVITES_PER_HOUR", 1),
            self.set_user(self.manager["user"]),
        ):
            invite_members(self.customer.name, [first], False)
            with self.assertRaises(frappe.RateLimitExceededError):
                invite_members(self.customer.name, [second], False)
        self.assertFalse(frappe.db.exists("User Invitation", {"email": second}))


class TestMemberRemoval(IntegrationTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        frappe.set_user("Administrator")
        cls.customer, cls.owner, cls.manager, cls.member = make_organization("Removal")
        cls.other_customer = create_customer(unique_name("Test Other Removal"))
        # Removing needs its own setting; cancelling an invitation needs the invite one.
        cls.enterClassContext(
            change_settings(
                "HD Settings",
                {
                    "allow_customer_managers_to_invite": 1,
                    "allow_customer_managers_to_manage_organization": 1,
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

    def test_a_removed_manager_loses_the_manager_role(self) -> None:
        with self.set_user(self.owner["user"]):
            remove_member(self.customer.name, self.manager["contact"])
        self.addCleanup(self.readd_manager)

        roles = frappe.get_roles(self.manager["user"])
        self.assertNotIn("HD Customer Manager", roles)
        self.assertIn("HD Customer", roles)

    def readd_manager(self) -> None:
        customer = frappe.get_doc("HD Customer", self.customer.name)
        customer.append(
            "contacts", {"contact_name": self.manager["contact"], "is_manager": 1}
        )
        customer.save()

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

    def test_removal_needs_the_member_management_setting(self) -> None:
        with (
            change_settings(
                "HD Settings", {"allow_customer_managers_to_manage_organization": 0}
            ),
            self.set_user(self.manager["user"]),
            self.assertRaises(frappe.PermissionError),
        ):
            remove_member(self.customer.name, self.member["contact"])

    def test_a_manager_cancels_an_invitation(self) -> None:
        newcomer = unique_email("newcomer")
        self.addCleanup(delete_invitations, newcomer)
        with self.set_user(self.manager["user"]):
            invite_members(self.customer.name, [newcomer], False)
            invitation = frappe.db.get_value("User Invitation", {"email": newcomer})
            cancel_invitation(self.customer.name, invitation)

        status = frappe.db.get_value("User Invitation", invitation, "status")
        self.assertEqual(status, "Cancelled")

    def test_another_organizations_invitation_is_refused(self) -> None:
        newcomer = unique_email("newcomer")
        invitation = make_invitation(newcomer, self.other_customer.name)
        self.addCleanup(delete_invitations, newcomer)

        with (
            self.set_user(self.manager["user"]),
            self.assertRaises(frappe.PermissionError),
        ):
            cancel_invitation(self.customer.name, invitation.name)


class TestOrganizationEdits(IntegrationTestCase):
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
                "HD Settings", {"allow_customer_managers_to_manage_organization": 1}
            )
        )

    def test_edits_need_the_portal_setting(self) -> None:
        with (
            change_settings(
                "HD Settings", {"allow_customer_managers_to_manage_organization": 0}
            ),
            self.set_user(self.manager["user"]),
            self.assertRaises(frappe.PermissionError),
        ):
            update_organization_image(self.customer.name, "/files/logo.png")

    def test_a_plain_member_cannot_edit(self) -> None:
        with (
            self.set_user(self.member["user"]),
            self.assertRaises(frappe.PermissionError),
        ):
            update_organization_image(self.customer.name, "/files/logo.png")

    def test_a_linked_logo_is_refused(self) -> None:
        with (
            self.set_user(self.manager["user"]),
            self.assertRaises(frappe.ValidationError),
        ):
            update_organization_image(self.customer.name, "https://tracker.test/a.png")

    def test_a_manager_can_set_and_clear_the_logo(self) -> None:
        with self.set_user(self.manager["user"]):
            update_organization_image(self.customer.name, "/files/logo.png")
        self.assertEqual(
            frappe.db.get_value("HD Customer", self.customer.name, "image"),
            "/files/logo.png",
        )
        with self.set_user(self.manager["user"]):
            update_organization_image(self.customer.name, "")
        self.assertIsNone(
            frappe.db.get_value("HD Customer", self.customer.name, "image")
        )

    def test_the_creator_s_email_is_not_shown_as_the_organization_s(self) -> None:
        with self.set_user(self.manager["user"]):
            self.assertIsNone(get_organization(self.customer.name)["email"])


class TestInvitableContacts(IntegrationTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        frappe.set_user("Administrator")
        cls.domain = f"{frappe.generate_hash(length=8)}.test"
        cls.manager = create_contact("Invite Manager", f"manager@{cls.domain}")
        cls.colleague = create_contact("Invite Colleague", f"colleague@{cls.domain}")
        cls.invitee = create_contact("Invite Invitee", f"invitee@{cls.domain}")
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

    def emails(self, query: str = "") -> list[str]:
        with self.set_user(self.manager["user"]):
            return [
                row.email for row in get_invitable_contacts(self.customer.name, query)
            ]

    def test_suggests_only_contacts_at_the_organization_domain(self) -> None:
        self.assertIn(self.colleague["user"], self.emails("Invite Colleague"))
        self.assertEqual(self.emails(self.outsider["user"]), [])

    def test_an_organization_without_a_domain_suggests_nobody(self) -> None:
        self.customer.db_set("domain", "")
        self.addCleanup(self.customer.db_set, "domain", self.domain)
        self.assertEqual(self.emails(self.colleague["user"]), [])

    def test_an_organization_on_a_public_domain_suggests_nobody(self) -> None:
        stranger = create_contact(
            "Invite Stranger", f"{frappe.generate_hash(length=8)}@gmail.com"
        )
        self.customer.db_set("domain", "Gmail.com")
        self.addCleanup(self.customer.db_set, "domain", self.domain)
        self.assertNotIn(stranger["user"], self.emails(stranger["user"]))
        self.assertEqual(self.emails(), [])

    def test_members_agents_and_pending_invitees_are_not_suggested(self) -> None:
        with self.set_user(self.manager["user"]):
            invite_members(self.customer.name, [self.invitee["user"]], False)
        self.addCleanup(delete_invitations, self.invitee["user"])

        emails = self.emails(self.domain)
        for person in (self.manager, self.agent, self.invitee):
            self.assertNotIn(person["user"], emails)

    def test_a_non_manager_cannot_read_the_suggestions(self) -> None:
        with (
            self.set_user(self.colleague["user"]),
            self.assertRaises(frappe.PermissionError),
        ):
            get_invitable_contacts(self.customer.name)


class TestOrganizationCards(IntegrationTestCase):
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

    def test_a_member_counts_only_the_tickets_they_can_open(self) -> None:
        customer, _owner, manager, member = make_organization("Card Count")
        for contact in (manager, member):
            ticket = make_ticket(subject="Card count ticket", raised_by=contact["user"])
            ticket.db_set("customer", customer.name, update_modified=False)

        def count(user: str) -> int:
            with self.set_user(user):
                return get_organization_card(customer.name)["ticket_count"]

        self.assertEqual(count(member["user"]), 1)
        self.assertEqual(count(manager["user"]), 2)

    def test_members_are_counted(self) -> None:
        self.assertEqual(self.card()["member_count"], 1)
