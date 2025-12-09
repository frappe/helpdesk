# Copyright (c) 2024, Frappe Technologies and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from helpdesk.helpdesk.doctype.hd_ticket_comment.hd_ticket_comment import (
    PRESET_EMOJIS,
    get_reactions,
    toggle_reaction,
)


class TestHDTicketComment(FrappeTestCase):
    """Test cases for HD Ticket Comment reactions functionality."""

    def setUp(self):
        """Set up test data before each test."""
        # Create test users
        if not frappe.db.exists("User", "test_user1@example.com"):
            frappe.get_doc(
                {
                    "doctype": "User",
                    "email": "test_user1@example.com",
                    "first_name": "Test",
                    "last_name": "User One",
                    "send_welcome_email": 0,
                }
            ).insert(ignore_permissions=True)

        if not frappe.db.exists("User", "test_user2@example.com"):
            frappe.get_doc(
                {
                    "doctype": "User",
                    "email": "test_user2@example.com",
                    "first_name": "Test",
                    "last_name": "User Two",
                    "send_welcome_email": 0,
                }
            ).insert(ignore_permissions=True)

        # Create test ticket (let frappe generate the name)
        self.test_ticket = frappe.get_doc(
            {
                "doctype": "HD Ticket",
                "subject": "Test Ticket for Reactions",
                "raised_by": "test_user1@example.com",
            }
        )
        self.test_ticket.insert(ignore_permissions=True)

        # Create test comment using the actual ticket name
        self.test_comment = frappe.get_doc(
            {
                "doctype": "HD Ticket Comment",
                "reference_ticket": self.test_ticket.name,
                "content": "<p>Test comment for reactions</p>",
                "commented_by": "test_user1@example.com",
            }
        )
        self.test_comment.insert(ignore_permissions=True)

    def tearDown(self):
        """Clean up after each test."""
        frappe.set_user("Administrator")
        
        # Delete test comment
        if hasattr(self, "test_comment") and self.test_comment:
            if frappe.db.exists("HD Ticket Comment", self.test_comment.name):
                frappe.delete_doc(
                    "HD Ticket Comment", self.test_comment.name, force=True
                )

        # Delete test ticket
        if hasattr(self, "test_ticket") and self.test_ticket:
            if frappe.db.exists("HD Ticket", self.test_ticket.name):
                frappe.delete_doc("HD Ticket", self.test_ticket.name, force=True)

    def test_one_reaction_per_user(self):
        """Test that a user can only have one reaction on a comment."""
        frappe.set_user("test_user2@example.com")

        # Add first reaction
        toggle_reaction(self.test_comment.name, "👍")

        # Check reaction was added
        doc = frappe.get_doc("HD Ticket Comment", self.test_comment.name)
        self.assertEqual(len(doc.reactions), 1)
        self.assertEqual(doc.reactions[0].emoji, "👍")
        self.assertEqual(doc.reactions[0].user, "test_user2@example.com")

        # Add different reaction - should replace previous
        toggle_reaction(self.test_comment.name, "❤️")

        # Reload and check only one reaction exists
        doc.reload()
        self.assertEqual(
            len(doc.reactions), 1, "User should have only one reaction at a time"
        )
        self.assertEqual(
            doc.reactions[0].emoji, "❤️", "Reaction should be replaced with new emoji"
        )

        # Toggle same emoji - should remove it
        toggle_reaction(self.test_comment.name, "❤️")

        doc.reload()
        self.assertEqual(len(doc.reactions), 0, "Reaction should be removed on toggle")

        frappe.set_user("Administrator")

    def test_reaction_count_accuracy(self):
        """Test that reaction counts are accurate for multiple users."""
        # Create more test users
        users = []
        for i in range(3, 13):
            email = f"test_user{i}@example.com"
            if not frappe.db.exists("User", email):
                user = frappe.get_doc(
                    {
                        "doctype": "User",
                        "email": email,
                        "first_name": f"User{i}",
                        "send_welcome_email": 0,
                    }
                )
                user.insert(ignore_permissions=True)
            users.append(email)

        # 10 users react with heart
        for user_email in users:
            frappe.set_user(user_email)
            toggle_reaction(self.test_comment.name, "❤️")

        # 3 users react with thumbs up (reusing first 3)
        for user_email in users[:3]:
            frappe.set_user(user_email)
            toggle_reaction(self.test_comment.name, "👍")

        frappe.set_user("Administrator")

        # Get reactions
        reactions = get_reactions(self.test_comment.name)

        # Find heart and thumbs up reactions
        heart_reaction = next((r for r in reactions if r["emoji"] == "❤️"), None)
        thumbs_reaction = next((r for r in reactions if r["emoji"] == "👍"), None)

        # Verify counts
        self.assertIsNotNone(heart_reaction, "Heart reaction should exist")
        self.assertEqual(
            heart_reaction["count"],
            7,
            "7 users should have heart reaction (10 - 3 who switched)",
        )

        self.assertIsNotNone(thumbs_reaction, "Thumbs up reaction should exist")
        self.assertEqual(
            thumbs_reaction["count"], 3, "3 users should have thumbs up reaction"
        )

        # Cleanup
        for email in users:
            if frappe.db.exists("User", email):
                frappe.delete_doc("User", email, force=True)

    def test_notification_created_on_reaction(self):
        """Test that a notification is created when someone reacts to a comment."""
        frappe.set_user("test_user1@example.com")

        # Get initial notification count
        initial_count = frappe.db.count(
            "HD Notification",
            {
                "user_to": "test_user1@example.com",
                "notification_type": "Reaction",
                "reference_comment": self.test_comment.name,
            },
        )

        # Switch to different user and add reaction
        frappe.set_user("test_user2@example.com")
        toggle_reaction(self.test_comment.name, "👍")

        frappe.set_user("Administrator")

        # Check notification was created
        final_count = frappe.db.count(
            "HD Notification",
            {
                "user_to": "test_user1@example.com",
                "notification_type": "Reaction",
                "reference_comment": self.test_comment.name,
            },
        )

        self.assertEqual(
            final_count,
            initial_count + 1,
            "A notification should be created when user reacts",
        )

        # Verify notification content
        notification = frappe.get_last_doc(
            "HD Notification",
            {
                "user_to": "test_user1@example.com",
                "notification_type": "Reaction",
                "reference_comment": self.test_comment.name,
            },
        )

        self.assertEqual(notification.user_from, "test_user2@example.com")
        self.assertIn("reacted with", notification.message)
        self.assertIn("👍", notification.message)
        self.assertIn("on your comment", notification.message)
        self.assertEqual(notification.reference_ticket, self.test_ticket.name)

        # Cleanup notification
        frappe.delete_doc("HD Notification", notification.name, force=True)

    def test_only_preset_emojis_allowed(self):
        """Test that only preset emojis can be added via API."""
        frappe.set_user("test_user2@example.com")

        # Try to add non-preset emoji
        invalid_emojis = ["🔥", "💯", "🚨", "😂"]

        for invalid_emoji in invalid_emojis:
            with self.assertRaises(frappe.ValidationError):
                toggle_reaction(self.test_comment.name, invalid_emoji)

        # Verify no reactions were added
        doc = frappe.get_doc("HD Ticket Comment", self.test_comment.name)
        self.assertEqual(len(doc.reactions), 0, "No invalid reactions should be added")

        # Verify all preset emojis are accepted
        for preset_emoji in PRESET_EMOJIS:
            toggle_reaction(self.test_comment.name, preset_emoji)
            doc.reload()
            self.assertEqual(
                doc.reactions[0].emoji,
                preset_emoji,
                f"Preset emoji {preset_emoji} should be accepted",
            )

        frappe.set_user("Administrator")

    def test_reaction_toggle_behavior(self):
        """Test that clicking same emoji again removes the reaction."""
        frappe.set_user("test_user2@example.com")

        # Add reaction
        result = toggle_reaction(self.test_comment.name, "👍")
        self.assertEqual(result["action"], "added")

        # Verify reaction exists
        doc = frappe.get_doc("HD Ticket Comment", self.test_comment.name)
        self.assertEqual(len(doc.reactions), 1)

        # Toggle same emoji
        result = toggle_reaction(self.test_comment.name, "👍")
        self.assertEqual(result["action"], "removed")

        # Verify reaction removed
        doc.reload()
        self.assertEqual(len(doc.reactions), 0)

        frappe.set_user("Administrator")

    def test_get_reactions_returns_correct_data(self):
        """Test that get_reactions API returns properly formatted data."""
        # Add reactions from different users
        frappe.set_user("test_user1@example.com")
        toggle_reaction(self.test_comment.name, "👍")

        frappe.set_user("test_user2@example.com")
        toggle_reaction(self.test_comment.name, "❤️")

        frappe.set_user("Administrator")

        # Get reactions
        reactions = get_reactions(self.test_comment.name)

        # Verify structure
        self.assertEqual(len(reactions), 2, "Should have 2 different reactions")

        for reaction in reactions:
            self.assertIn("emoji", reaction)
            self.assertIn("count", reaction)
            self.assertIn("users", reaction)
            self.assertIn("current_user_reacted", reaction)
            self.assertEqual(reaction["count"], len(reaction["users"]))

            for user in reaction["users"]:
                self.assertIn("user", user)
                self.assertIn("full_name", user)
