# Copyright (c) 2024, Frappe Technologies and Contributors
# See license.txt

import frappe
from frappe.desk.form.assign_to import remove
from frappe.tests.utils import FrappeTestCase

from helpdesk.api.ticket import assign_ticket_to_agent
from helpdesk.helpdesk.doctype.hd_ticket_comment.hd_ticket_comment import (
    PRESET_EMOJIS,
    get_reactions,
    toggle_reaction,
)
from helpdesk.test_utils import create_agent


class TestHDTicketComment(FrappeTestCase):
    def setUp(self):
        frappe.db.set_single_value("HD Settings", "enable_comment_reactions", 1)

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

        self.agent_emails = [f"agent{i}@example.com" for i in range(1, 13)]
        for email in self.agent_emails:
            create_agent(email)

        self.assigned_agents = set()

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

    def assign_agent(self, user: str):
        assign_ticket_to_agent(self.test_ticket.name, user)
        self.assigned_agents.add(user)

    def unassign_agent(self, user: str):
        remove("HD Ticket", self.test_ticket.name, user)

    def tearDown(self):
        frappe.set_user("Administrator")

        for user in list(self.assigned_agents):
            self.unassign_agent(user)
        self.assigned_agents.clear()

        if hasattr(self, "test_comment") and self.test_comment:
            if frappe.db.exists("HD Ticket Comment", self.test_comment.name):
                frappe.delete_doc(
                    "HD Ticket Comment", self.test_comment.name, force=True
                )

        if hasattr(self, "test_ticket") and self.test_ticket:
            if frappe.db.exists("HD Ticket", self.test_ticket.name):
                frappe.delete_doc("HD Ticket", self.test_ticket.name, force=True)

        for email in self.agent_emails:
            if frappe.db.exists("User", email):
                frappe.delete_doc("User", email, force=True)

        frappe.db.set_single_value("HD Settings", "enable_comment_reactions", 0)

    def test_one_reaction_per_user(self):
        agent = self.agent_emails[0]
        frappe.set_user(agent)
        self.assign_agent(agent)

        toggle_reaction(self.test_comment.name, "👍")

        doc = frappe.get_doc("HD Ticket Comment", self.test_comment.name)
        self.assertEqual(len(doc.reactions), 1)
        self.assertEqual(doc.reactions[0].emoji, "👍")
        self.assertEqual(doc.reactions[0].user, agent)

        toggle_reaction(self.test_comment.name, "❤️")

        doc.reload()
        self.assertEqual(len(doc.reactions), 1)
        self.assertEqual(doc.reactions[0].emoji, "❤️")

        toggle_reaction(self.test_comment.name, "❤️")

        doc.reload()
        self.assertEqual(len(doc.reactions), 0)

        frappe.set_user("Administrator")

    def test_reaction_count_accuracy(self):
        users = self.agent_emails[1:11]

        for user_email in users:
            frappe.set_user(user_email)
            self.assign_agent(user_email)
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

        agent = self.agent_emails[0]
        frappe.set_user(agent)
        self.assign_agent(agent)
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

        self.assertEqual(notification.user_from, agent)
        self.assertEqual(notification.message, "1 person reacted to your comment")
        self.assertEqual(str(notification.reference_ticket), str(self.test_ticket.name))

        frappe.delete_doc("HD Notification", notification.name, force=True)

    def test_only_preset_emojis_allowed(self):
        agent = self.agent_emails[0]
        frappe.set_user(agent)
        self.assign_agent(agent)

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
        agent = self.agent_emails[0]
        frappe.set_user(agent)
        self.assign_agent(agent)

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
        agent_one = self.agent_emails[0]
        agent_two = self.agent_emails[1]
        frappe.set_user(agent_one)
        self.assign_agent(agent_one)
        toggle_reaction(self.test_comment.name, "👍")

        frappe.set_user(agent_two)
        self.assign_agent(agent_two)
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
        agent = self.agent_emails[2]
        agent_comment = frappe.get_doc(
            {
                "doctype": "HD Ticket Comment",
                "reference_ticket": self.test_ticket.name,
                "content": "<p>Agent self reaction test</p>",
                "commented_by": agent,
            }
        )
        agent_comment.insert(ignore_permissions=True)

        frappe.set_user(agent)
        self.assign_agent(agent)

        initial_count = frappe.db.count(
            "HD Notification",
            {
                "user_to": agent,
                "notification_type": "Reaction",
                "reference_comment": agent_comment.name,
            },
        )

        toggle_reaction(agent_comment.name, "👍")

        frappe.set_user("Administrator")

        final_count = frappe.db.count(
            "HD Notification",
            {
                "user_to": agent,
                "notification_type": "Reaction",
                "reference_comment": agent_comment.name,
            },
        )

        self.assertEqual(final_count, initial_count)

        frappe.delete_doc("HD Ticket Comment", agent_comment.name, force=True)

    def test_grouped_notifications(self):
        test_users = self.agent_emails[3:6]

        agent = self.agent_emails[0]
        frappe.set_user(agent)
        self.assign_agent(agent)
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
        self.assign_agent(test_users[0])
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
        self.assertEqual(notification.message, "2 people reacted to your comment")

        frappe.delete_doc("HD Notification", notification.name, force=True)
