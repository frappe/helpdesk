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
    def setUp(self):
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

        self.test_ticket = frappe.get_doc(
            {
                "doctype": "HD Ticket",
                "subject": "Test Ticket for Reactions",
                "raised_by": "test_user1@example.com",
            }
        )
        self.test_ticket.insert(ignore_permissions=True)

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
        frappe.set_user("Administrator")

        if hasattr(self, "test_comment") and self.test_comment:
            if frappe.db.exists("HD Ticket Comment", self.test_comment.name):
                frappe.delete_doc(
                    "HD Ticket Comment", self.test_comment.name, force=True
                )

        if hasattr(self, "test_ticket") and self.test_ticket:
            if frappe.db.exists("HD Ticket", self.test_ticket.name):
                frappe.delete_doc("HD Ticket", self.test_ticket.name, force=True)

    def test_one_reaction_per_user(self):
        frappe.set_user("test_user2@example.com")

        toggle_reaction(self.test_comment.name, "👍")

        doc = frappe.get_doc("HD Ticket Comment", self.test_comment.name)
        self.assertEqual(len(doc.reactions), 1)
        self.assertEqual(doc.reactions[0].emoji, "👍")
        self.assertEqual(doc.reactions[0].user, "test_user2@example.com")

        toggle_reaction(self.test_comment.name, "❤️")

        doc.reload()
        self.assertEqual(len(doc.reactions), 1)
        self.assertEqual(doc.reactions[0].emoji, "❤️")

        toggle_reaction(self.test_comment.name, "❤️")

        doc.reload()
        self.assertEqual(len(doc.reactions), 0)

        frappe.set_user("Administrator")

    def test_reaction_count_accuracy(self):
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

        for user_email in users:
            frappe.set_user(user_email)
            toggle_reaction(self.test_comment.name, "❤️")

        for user_email in users[:3]:
            frappe.set_user(user_email)
            toggle_reaction(self.test_comment.name, "👍")

        frappe.set_user("Administrator")

        reactions = get_reactions(self.test_comment.name)

        heart_reaction = next((r for r in reactions if r["emoji"] == "❤️"), None)
        thumbs_reaction = next((r for r in reactions if r["emoji"] == "👍"), None)

        self.assertIsNotNone(heart_reaction)
        self.assertEqual(heart_reaction["count"], 7)

        self.assertIsNotNone(thumbs_reaction)
        self.assertEqual(thumbs_reaction["count"], 3)

        for email in users:
            if frappe.db.exists("User", email):
                frappe.delete_doc("User", email, force=True)

    def test_notification_created_on_reaction(self):
        frappe.set_user("test_user1@example.com")

        initial_count = frappe.db.count(
            "HD Notification",
            {
                "user_to": "test_user1@example.com",
                "notification_type": "Reaction",
                "reference_comment": self.test_comment.name,
            },
        )

        frappe.set_user("test_user2@example.com")
        toggle_reaction(self.test_comment.name, "👍")

        frappe.set_user("Administrator")

        final_count = frappe.db.count(
            "HD Notification",
            {
                "user_to": "test_user1@example.com",
                "notification_type": "Reaction",
                "reference_comment": self.test_comment.name,
            },
        )

        self.assertEqual(final_count, initial_count + 1)

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
        self.assertEqual(str(notification.reference_ticket), str(self.test_ticket.name))

        frappe.delete_doc("HD Notification", notification.name, force=True)

    def test_only_preset_emojis_allowed(self):
        frappe.set_user("test_user2@example.com")

        invalid_emojis = ["🔥", "💯", "🚨", "😂"]

        for invalid_emoji in invalid_emojis:
            with self.assertRaises(frappe.ValidationError):
                toggle_reaction(self.test_comment.name, invalid_emoji)

        doc = frappe.get_doc("HD Ticket Comment", self.test_comment.name)
        self.assertEqual(len(doc.reactions), 0)

        for preset_emoji in PRESET_EMOJIS:
            toggle_reaction(self.test_comment.name, preset_emoji)
            doc.reload()
            self.assertEqual(doc.reactions[0].emoji, preset_emoji)

        frappe.set_user("Administrator")

    def test_reaction_toggle_behavior(self):
        frappe.set_user("test_user2@example.com")

        result = toggle_reaction(self.test_comment.name, "👍")
        self.assertEqual(result["action"], "added")

        doc = frappe.get_doc("HD Ticket Comment", self.test_comment.name)
        self.assertEqual(len(doc.reactions), 1)

        result = toggle_reaction(self.test_comment.name, "👍")
        self.assertEqual(result["action"], "removed")

        doc.reload()
        self.assertEqual(len(doc.reactions), 0)

        frappe.set_user("Administrator")

    def test_get_reactions_returns_correct_data(self):
        frappe.set_user("test_user1@example.com")
        toggle_reaction(self.test_comment.name, "👍")

        frappe.set_user("test_user2@example.com")
        toggle_reaction(self.test_comment.name, "❤️")

        frappe.set_user("Administrator")

        reactions = get_reactions(self.test_comment.name)

        self.assertEqual(len(reactions), 2)

        for reaction in reactions:
            self.assertIn("emoji", reaction)
            self.assertIn("count", reaction)
            self.assertIn("users", reaction)
            self.assertIn("current_user_reacted", reaction)
            self.assertEqual(reaction["count"], len(reaction["users"]))

            for user in reaction["users"]:
                self.assertIn("user", user)
                self.assertIn("full_name", user)

    def test_no_notification_for_self_reaction(self):
        frappe.set_user("test_user1@example.com")

        initial_count = frappe.db.count(
            "HD Notification",
            {
                "user_to": "test_user1@example.com",
                "notification_type": "Reaction",
                "reference_comment": self.test_comment.name,
            },
        )

        toggle_reaction(self.test_comment.name, "👍")

        frappe.set_user("Administrator")

        final_count = frappe.db.count(
            "HD Notification",
            {
                "user_to": "test_user1@example.com",
                "notification_type": "Reaction",
                "reference_comment": self.test_comment.name,
            },
        )

        self.assertEqual(final_count, initial_count)

    def test_grouped_notifications(self):
        test_users = []
        for i in range(3, 6):
            email = f"test_user{i}@example.com"
            if not frappe.db.exists("User", email):
                frappe.get_doc(
                    {
                        "doctype": "User",
                        "email": email,
                        "first_name": f"User{i}",
                        "send_welcome_email": 0,
                    }
                ).insert(ignore_permissions=True)
            test_users.append(email)

        frappe.set_user("test_user2@example.com")
        toggle_reaction(self.test_comment.name, "👍")

        frappe.set_user("Administrator")

        notifications = frappe.get_all(
            "HD Notification",
            filters={
                "user_to": "test_user1@example.com",
                "notification_type": "Reaction",
                "reference_comment": self.test_comment.name,
            },
        )
        self.assertEqual(len(notifications), 1)

        frappe.set_user(test_users[0])
        toggle_reaction(self.test_comment.name, "❤️")

        frappe.set_user("Administrator")

        notifications = frappe.get_all(
            "HD Notification",
            filters={
                "user_to": "test_user1@example.com",
                "notification_type": "Reaction",
                "reference_comment": self.test_comment.name,
            },
        )
        self.assertEqual(len(notifications), 1)

        notification = frappe.get_doc("HD Notification", notifications[0].name)
        self.assertIn("reacted on your comment", notification.message)

        frappe.delete_doc("HD Notification", notification.name, force=True)
        for email in test_users:
            if frappe.db.exists("User", email):
                frappe.delete_doc("User", email, force=True)
