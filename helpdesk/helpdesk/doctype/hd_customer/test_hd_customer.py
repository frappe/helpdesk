# Copyright (c) 2022, Frappe Technologies and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.helpdesk.doctype.hd_customer.hd_customer import (
    has_permission,
    permission_query,
)
from helpdesk.helpdesk.hooks.user_invitation import after_accept
from helpdesk.test_utils import (
    add_contact_in_customer,
    create_contact,
    create_customer,
    create_user,
    get_invitation,
    get_roles,
    make_ticket,
    update_role_in_customer,
)


class TestHDCustomer(IntegrationTestCase):
    def setUp(self) -> None:
        frappe.set_user("Administrator")

    def tearDown(self) -> None:
        frappe.set_user("Administrator")

    def test_contact_with_linked_user_is_added_directly(self) -> None:
        customer = create_customer("Test Customer Direct Add")
        contact = create_contact("Linked", "linked-contact@example.com")

        result = customer.add_contacts([contact["contact"]], "HD Customer")

        self.assertIn(contact["contact"], result["added"])
        self.assertEqual(result["invite_result"]["invited_emails"], [])
        member_names = [row.contact_name for row in customer.contacts]
        self.assertIn(contact["contact"], member_names)
        self.assertFalse(get_invitation(contact["user"]), "No invitation expected")

    def test_contact_without_user_gets_invited_not_added(self) -> None:
        customer = create_customer("Test Customer Invite Contact")
        email = "unlinked-contact@example.com"
        contact = create_contact("Unlinked", email, user=False)

        result = customer.add_contacts([contact["contact"]], "HD Customer")

        self.assertFalse(result["added"])
        self.assertIn(email, result["invite_result"]["invited_emails"])
        member_names = [row.contact_name for row in customer.contacts]
        self.assertNotIn(contact["contact"], member_names)
        self.assertFalse(
            frappe.db.exists("User", email),
            "No user should be auto created for an unlinked contact",
        )
        invitation = get_invitation(email)
        self.assertEqual(invitation.customer, customer.name)
        self.assertEqual(invitation.contact, contact["contact"])

    def test_unknown_email_gets_invited(self) -> None:
        customer = create_customer("Test Customer Invite Email")

        result = customer.add_contacts(["fresh-person@example.com"], "HD Customer")

        self.assertIn(
            "fresh-person@example.com", result["invite_result"]["invited_emails"]
        )
        invitation = get_invitation("fresh-person@example.com")
        self.assertEqual(invitation.customer, customer.name)

    def test_duplicate_contact_is_not_added_twice(self) -> None:
        customer = create_customer("Test Customer Duplicate")
        contact = create_contact("Duplicate", "duplicate-contact@example.com")

        customer.add_contacts([contact["contact"]], "HD Customer")
        result = customer.add_contacts([contact["contact"]], "HD Customer")

        self.assertFalse(result["added"])
        member_names = [row.contact_name for row in customer.contacts]
        self.assertEqual(member_names.count(contact["contact"]), 1)

    def test_manager_role_is_applied_on_add(self) -> None:
        customer = create_customer("Test Customer Manager Role")
        contact = create_contact("Manager", "manager-contact@example.com")

        customer.add_contacts([contact["contact"]], "HD Customer Manager")

        member = next(
            row for row in customer.contacts if row.contact_name == contact["contact"]
        )
        self.assertTrue(member.is_manager)
        self.assertIn("HD Customer Manager", get_roles(contact["user"]))

    def test_add_contacts_requires_manager_roles(self) -> None:
        customer = create_customer("Test Customer Permission")
        user = create_user("no-permission@example.com")

        frappe.set_user(user.name)
        with self.assertRaises(frappe.PermissionError):
            customer.add_contacts(["anyone@example.com"], "HD Customer")

    def test_save_does_not_auto_create_user(self) -> None:
        customer = create_customer("Test Customer No Auto User")
        email = "no-auto-user@example.com"
        contact = create_contact("No User", email, user=False)

        customer.append("contacts", {"contact_name": contact["contact"]})
        customer.save()

        self.assertFalse(frappe.db.exists("User", email))
        self.assertFalse(get_invitation(email))

    def test_accepted_invitation_links_contact_to_customer(self) -> None:
        customer = create_customer("Test Customer Accept Invite")
        email = "accepted-invite@example.com"
        customer.add_contacts([email], "HD Customer")
        invitation = frappe.get_doc("User Invitation", get_invitation(email).name)
        user = create_user(email)

        after_accept(invitation, user, user_inserted=True)

        customer.reload()
        contact = frappe.db.get_value("Contact", {"user": user.name, "email_id": email})
        member_names = [row.contact_name for row in customer.contacts]
        self.assertIn(contact, member_names)

    def test_setting_primary_contact_makes_them_manager(self) -> None:
        customer = create_customer("Test Customer Primary Manager")
        first = create_contact("First", "primary-mgr-1@example.com")
        second = create_contact("Second", "primary-mgr-2@example.com")

        # no primary yet, so neither contact is a manager
        customer.add_contacts([first["contact"], second["contact"]], "HD Customer")
        self.assertNotIn("HD Customer Manager", get_roles(second["user"]))

        # designating a primary promotes that contact to manager
        customer.primary_contact = second["contact"]
        customer.save()

        member = next(
            row for row in customer.contacts if row.contact_name == second["contact"]
        )
        self.assertTrue(member.is_manager)
        self.assertIn("HD Customer Manager", get_roles(second["user"]))

    def test_customer_roles_follow_is_manager(self) -> None:
        customer = create_customer("Test Customer Roles")
        manager = create_contact("RoleManager", "role-manager@example.com")
        member = create_contact("RoleMember", "role-member@example.com")

        customer.add_contacts([manager["contact"]], "HD Customer Manager")
        customer.add_contacts([member["contact"]], "HD Customer")

        self.assertIn("HD Customer Manager", get_roles(manager["user"]))
        member_roles = get_roles(member["user"])
        self.assertIn("HD Customer", member_roles)
        self.assertNotIn("HD Customer Manager", member_roles)

        # promote the non-primary member, then demote; the manager role is revoked
        update_role_in_customer(customer, member["contact"], "HD Customer Manager")
        self.assertIn("HD Customer Manager", get_roles(member["user"]))
        update_role_in_customer(customer, member["contact"], "HD Customer")
        demoted_roles = get_roles(member["user"])
        self.assertNotIn("HD Customer Manager", demoted_roles)
        self.assertIn("HD Customer", demoted_roles)

    def test_duplicate_contacts_are_rejected_on_save(self) -> None:
        customer = create_customer("Test Customer Duplicate Validate")
        contact = create_contact("DupValidate", "dup-validate@example.com", user=False)

        customer.append("contacts", {"contact_name": contact["contact"]})
        customer.append("contacts", {"contact_name": contact["contact"]})

        with self.assertRaises(frappe.ValidationError):
            customer.save()

    def test_create_customer_with_primary_contact(self) -> None:
        from helpdesk.api.customer import create_customer as create_customer_api

        email = "primary-contact-api@example.com"
        cleanup_customer_and_contact("Test Customer API Primary", email)

        name = create_customer_api(
            {"customer_name": "Test Customer API Primary", "customer_type": "Company"},
            {"first_name": "Primary", "last_name": "Contact", "email": email},
        )

        customer = frappe.get_doc("HD Customer", name)
        contact = frappe.db.get_value("Contact", {"email_id": email}, "name")
        self.assertEqual(customer.customer_type, "Company")
        self.assertEqual(customer.primary_contact, contact)
        member = next(row for row in customer.contacts if row.contact_name == contact)
        self.assertTrue(member.is_manager)
        invitation = get_invitation(email)
        self.assertEqual(invitation.customer, name)
        self.assertEqual(invitation.contact, contact)

    def test_primary_contact_not_duplicated_after_accept(self) -> None:
        from helpdesk.api.customer import create_customer as create_customer_api

        email = "primary-accept-api@example.com"
        cleanup_customer_and_contact("Test Customer API Accept", email)

        name = create_customer_api(
            {"customer_name": "Test Customer API Accept", "customer_type": "Company"},
            {"first_name": "Primary", "email": email},
        )
        invitation = frappe.get_doc("User Invitation", get_invitation(email).name)
        user = create_user(email)

        after_accept(invitation, user, user_inserted=True)

        customer = frappe.get_doc("HD Customer", name)
        contact = frappe.db.get_value("Contact", {"email_id": email}, "name")
        member_names = [row.contact_name for row in customer.contacts]
        self.assertEqual(member_names.count(contact), 1)

    def test_delete_customer_unlinks_tickets_and_invitations(self) -> None:
        from helpdesk.api.customer import delete_customer

        email = "delete-customer-unlink@example.com"
        contact, customer, ticket, invitation = self.setup_customer_for_delete(
            "Test Customer Unlink", email
        )

        delete_customer(customer.name)

        self.assertFalse(frappe.db.exists("HD Customer", customer.name))
        ticket.reload()
        self.assertIsNone(ticket.customer)
        invitation.reload()
        self.assertIsNone(invitation.customer)
        self.assertTrue(frappe.db.exists("Contact", contact["contact"]))

    def test_delete_customer_deletes_linked_tickets(self) -> None:
        from helpdesk.api.customer import delete_customer

        email = "delete-customer-tickets@example.com"
        contact, customer, ticket, invitation = self.setup_customer_for_delete(
            "Test Customer Delete Tickets", email
        )

        delete_customer(customer.name, delete_tickets=True)

        self.assertFalse(frappe.db.exists("HD Customer", customer.name))
        self.assertFalse(frappe.db.exists("HD Ticket", ticket.name))
        invitation.reload()
        self.assertIsNone(invitation.customer)
        self.assertTrue(frappe.db.exists("Contact", contact["contact"]))

    def setup_customer_for_delete(self, customer_name: str, email: str):
        for inv in frappe.db.get_all("User Invitation", {"email": email}, pluck="name"):
            frappe.delete_doc("User Invitation", inv, force=True)

        contact_doc = create_contact("DeleteLink", email, user=False)
        customer = create_customer(
            customer_name, [{"contact_name": contact_doc["contact"]}]
        )
        ticket = make_ticket(customer=customer.name, contact=contact_doc["contact"])
        invitation = frappe.get_doc(
            {
                "doctype": "User Invitation",
                "email": email,
                "app_name": "helpdesk",
                "redirect_to_path": "/helpdesk",
                "roles": [{"role": "HD Customer"}],
                "customer": customer.name,
                "contact": contact_doc["contact"],
            }
        ).insert(ignore_permissions=True)
        return contact_doc, customer, ticket, invitation

    def test_has_permission_member_reads_manager_writes(self) -> None:
        # Members may read their customer; only managers may write it.
        customer = create_customer("Perm Member Manager")
        member = create_contact("PermMember", "perm-member@example.com")
        manager = create_contact("PermManager", "perm-manager@example.com")
        add_contact_in_customer(customer, member["contact"], is_manager=False)
        add_contact_in_customer(customer, manager["contact"], is_manager=True)
        name = customer.name

        frappe.set_user(member["user"])
        self.assertTrue(frappe.has_permission("HD Customer", "read", name))
        self.assertFalse(frappe.has_permission("HD Customer", "write", name))
        frappe.set_user(manager["user"])
        self.assertTrue(frappe.has_permission("HD Customer", "read", name))
        self.assertTrue(frappe.has_permission("HD Customer", "write", name))

    def test_has_permission_denies_non_member(self) -> None:
        # A portal user who is not a member is denied read and write (IDOR guard).
        customer = create_customer("Perm Non Member")
        outsider = create_contact("PermOutsider", "perm-outsider@example.com")
        name = customer.name

        frappe.set_user(outsider["user"])
        self.assertFalse(frappe.has_permission("HD Customer", "read", name))
        self.assertFalse(frappe.has_permission("HD Customer", "write", name))

    def test_has_permission_per_record_role(self) -> None:
        # Manager of one customer who is only a member of another can write the
        # first but not the second; the role is bound per record, not per user.
        customer_a = create_customer("Perm Record A")
        customer_b = create_customer("Perm Record B")
        contact_in_dual_customers = create_contact("PermDual", "perm-dual@example.com")
        add_contact_in_customer(
            customer_a, contact_in_dual_customers["contact"], is_manager=True
        )
        add_contact_in_customer(
            customer_b, contact_in_dual_customers["contact"], is_manager=False
        )
        user = contact_in_dual_customers["user"]

        frappe.set_user(user)
        self.assertTrue(has_permission(customer_a, "read", user))
        self.assertTrue(has_permission(customer_a, "write", user))

        self.assertTrue(has_permission(customer_b, "read", user))
        self.assertFalse(has_permission(customer_b, "write", user))

    def test_permission_query_scopes_list(self) -> None:
        # Agents are unrestricted, members see only their customers, others none.
        agent = create_user("perm-query-agent@example.com")
        agent.add_roles("Agent")
        stranger = create_user("perm-query-stranger@example.com")
        member = create_contact("PermQueryMember", "perm-query-member@example.com")
        mine = create_customer("O'Brien Inc")  # apostrophe exercises SQL escaping
        other = create_customer("Perm Query Other")
        add_contact_in_customer(mine, member["contact"], is_manager=False)

        frappe.set_user(agent.name)
        self.assertEqual(permission_query(agent.name), "")
        frappe.set_user(stranger.name)
        self.assertEqual(permission_query(stranger.name), "1=0")
        frappe.set_user(member["user"])
        names = frappe.get_list("HD Customer", pluck="name")
        frappe.set_user("Administrator")
        self.assertIn(mine.name, names)
        self.assertNotIn(other.name, names)

    def test_has_permission_follows_live_role_change(self) -> None:
        # Write access tracks the live is_manager flag, not a cached role.
        # update_role_in_customer()
        customer = create_customer("Perm Live Change")
        member = create_contact("PermLive", "perm-live@example.com")
        add_contact_in_customer(customer, member["contact"], is_manager=False)
        user = member["user"]

        frappe.set_user(user)
        self.assertFalse(has_permission(customer, "write", user))
        update_role_in_customer(customer, member["contact"], "HD Customer Manager")
        frappe.set_user(user)
        self.assertTrue(has_permission(customer, "write", user))
        update_role_in_customer(customer, member["contact"], "HD Customer")
        frappe.set_user(user)
        self.assertFalse(has_permission(customer, "write", user))

    def test_primary_contact_must_be_a_listed_contact(self) -> None:
        customer = create_customer("Test Customer Primary Validate")
        contact = create_contact(
            "PrimaryValidate", "primary-validate@example.com", user=False
        )

        customer.append("contacts", {"contact_name": contact["contact"]})
        customer.primary_contact = "Non Existent Contact"

        with self.assertRaises(frappe.ValidationError):
            customer.save()


def cleanup_customer_and_contact(customer_name: str, email: str) -> None:
    if frappe.db.exists("HD Customer", customer_name):
        frappe.delete_doc("HD Customer", customer_name, force=True)
    for c in frappe.db.get_all("Contact", {"email_id": email}, pluck="name"):
        frappe.delete_doc("Contact", c, force=True)
    if frappe.db.exists("User", email):
        frappe.delete_doc("User", email, force=True)
