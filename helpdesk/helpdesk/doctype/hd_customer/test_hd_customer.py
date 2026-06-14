# Copyright (c) 2022, Frappe Technologies and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.helpdesk.hooks.user_invitation import after_accept
from helpdesk.test_utils import (
    create_contact,
    create_customer,
    create_user,
    get_invitation,
    get_roles,
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

    def test_primary_contact_is_forced_to_manager(self) -> None:
        customer = create_customer("Test Customer Primary Manager")
        contact = create_contact("Primary", "primary-manager@example.com")

        # added as a regular customer, but it is the only (hence primary) contact
        customer.add_contacts([contact["contact"]], "HD Customer")

        self.assertEqual(customer.primary_contact, contact["contact"])
        member = next(
            row for row in customer.contacts if row.contact_name == contact["contact"]
        )
        self.assertTrue(member.is_manager)

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

    def test_primary_contact_must_be_a_listed_contact(self) -> None:
        customer = create_customer("Test Customer Primary Validate")
        contact = create_contact(
            "PrimaryValidate", "primary-validate@example.com", user=False
        )

        customer.append("contacts", {"contact_name": contact["contact"]})
        customer.primary_contact = "Non Existent Contact"

        with self.assertRaises(frappe.ValidationError):
            customer.save()
