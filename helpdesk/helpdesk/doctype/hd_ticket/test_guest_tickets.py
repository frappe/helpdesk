import frappe
from frappe.handler import run_doc_method
from frappe.tests import IntegrationTestCase

from helpdesk.helpdesk.doctype.hd_ticket.hd_ticket import (
    has_permission,
    permission_query,
)
from helpdesk.patches.rebuild_guest_ticket_permissions import (
    execute as rebuild_guest_ticket_permissions,
)
from helpdesk.test_utils import (
    enable_guest_tickets,
    guest_ticket_rules,
    make_agent_manager,
    raise_guest_ticket,
    upload_test_file,
)


class TestGuestTickets(IntegrationTestCase):
    """With `allow_anyone_to_create_tickets` on, a guest may raise a ticket but never
    read, edit or list one. Every guest ticket is owned by the same user, "Guest", so
    any read would expose all of them."""

    def setUp(self):
        frappe.set_user("Administrator")
        self.addCleanup(
            enable_guest_tickets,
            frappe.db.get_single_value("HD Settings", "allow_anyone_to_create_tickets"),
        )
        enable_guest_tickets()

    def tearDown(self):
        frappe.set_user("Administrator")

    def test_guest_can_raise_a_ticket(self):
        ticket_name = raise_guest_ticket(self, "first.guest@example.com")
        self.assertEqual(
            frappe.db.get_value("HD Ticket", ticket_name, "owner"), "Guest"
        )
        # the description becomes the ticket's first message, from the guest's email
        self.assertEqual(
            frappe.db.get_value(
                "Communication", {"reference_name": ticket_name}, "sender"
            ),
            "first.guest@example.com",
        )

    def test_guest_cannot_read_edit_or_list_guest_tickets(self):
        ticket_names = [
            raise_guest_ticket(self, "victim.guest@example.com"),
            raise_guest_ticket(self, "attacker.guest@example.com"),
        ]
        frappe.set_user("Guest")
        for ticket_name in ticket_names:
            self.assertFalse(frappe.has_permission("HD Ticket", "read", ticket_name))
            self.assertFalse(frappe.has_permission("HD Ticket", "write", ticket_name))
        with self.assertRaises(frappe.PermissionError):
            frappe.get_list("HD Ticket")

    def test_guest_cannot_reply_on_a_guest_ticket(self):
        """The whitelisted reply method is the one write path left on a raised ticket."""
        ticket_name = raise_guest_ticket(self, "replied.guest@example.com")
        replies = frappe.db.count("Communication", {"reference_name": ticket_name})
        frappe.set_user("Guest")
        with self.assertRaises(frappe.PermissionError):
            run_doc_method(
                "create_communication_via_contact",
                dt="HD Ticket",
                dn=ticket_name,
                args={"message": "injected"},
            )
        frappe.set_user("Administrator")
        self.assertEqual(
            frappe.db.count("Communication", {"reference_name": ticket_name}), replies
        )

    def test_guest_cannot_read_a_private_attachment_of_a_guest_ticket(self):
        """Private files inherit read from the ticket they are attached to."""
        ticket_name = raise_guest_ticket(self, "private.guest@example.com")
        file_name = upload_test_file("gmail.png")
        self.addCleanup(frappe.delete_doc, "File", file_name, force=True)
        frappe.db.set_value(
            "File",
            file_name,
            {"attached_to_doctype": "HD Ticket", "attached_to_name": ticket_name},
        )
        frappe.set_user("Guest")
        self.assertFalse(frappe.has_permission("File", "read", file_name))

    def test_inline_image_of_a_guest_ticket_is_attached_to_it(self):
        frappe.set_user("Guest")
        # guest uploads are saved without permission checks, as upload_file does
        image = frappe.get_doc(
            {"doctype": "File", "file_name": "guest.png", "content": b"png"}
        ).insert(ignore_permissions=True)
        self.addCleanup(frappe.delete_doc, "File", image.name, force=True)
        ticket_name = raise_guest_ticket(
            self, "inline.guest@example.com", f'<img src="{image.file_url}">'
        )
        self.assertEqual(
            frappe.db.get_value("File", image.name, "attached_to_name"), ticket_name
        )

    def test_hooks_deny_guest_even_when_a_read_rule_is_granted(self):
        """A read rule added by hand in Role Permissions must still expose nothing."""
        ticket = frappe.get_doc(
            "HD Ticket", raise_guest_ticket(self, "hooks.guest@example.com")
        )
        self.assertTrue(has_permission(ticket, user="Guest", ptype="create"))
        self.assertFalse(has_permission(ticket, user="Guest", ptype="read"))
        self.assertFalse(has_permission(ticket, user="Guest", ptype="write"))
        self.assertEqual(permission_query("Guest"), "false")

    def test_settings_saves_keep_one_create_only_rule(self):
        enable_guest_tickets()
        # a repeat save must not stack a second rule
        self.assertEqual(
            guest_ticket_rules(),
            [{"read": 0, "write": 0, "create": 1, "export": 0, "if_owner": 0}],
        )
        enable_guest_tickets(False)
        self.assertEqual(guest_ticket_rules(), [])

    def test_agent_manager_can_toggle_guest_tickets(self):
        """Role rules are System Manager only, but this setting is not."""
        with self.set_user(make_agent_manager("guest-toggle")):
            enable_guest_tickets(False)
            enable_guest_tickets()
        self.assertEqual(
            guest_ticket_rules(),
            [{"read": 0, "write": 0, "create": 1, "export": 0, "if_owner": 0}],
        )

    def test_patch_collapses_stacked_owner_rules(self):
        """Older releases left one read/write/if_owner rule per settings save."""
        for _ in range(3):
            frappe.get_doc(
                {
                    "doctype": "Custom DocPerm",
                    "parent": "HD Ticket",
                    "parenttype": "DocType",
                    "parentfield": "permissions",
                    "role": "Guest",
                    "read": 1,
                    "write": 1,
                    "create": 1,
                    "if_owner": 1,
                }
            ).insert(ignore_permissions=True)
        rebuild_guest_ticket_permissions()
        self.assertEqual(
            guest_ticket_rules(),
            [{"read": 0, "write": 0, "create": 1, "export": 0, "if_owner": 0}],
        )
