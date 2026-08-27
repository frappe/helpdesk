# Copyright (c) 2026, Frappe Technologies and Contributors
# See license.txt

import json

import frappe
from frappe.cache_manager import clear_doctype_map
from frappe.tests import IntegrationTestCase

from helpdesk.api.saved_replies import (
    apply_saved_reply_actions,
    get_rendered_saved_reply,
)
from helpdesk.test_utils import make_agent, make_status, make_team, make_ticket

AGENT = "saved_reply_action_agent@test.com"
TEAM = "Saved Reply Action Team"
TICKET_TYPE = "Saved Reply Action Type"


def make_ticket_type(name):
    if not frappe.db.exists("HD Ticket Type", name):
        frappe.get_doc({"doctype": "HD Ticket Type", "name": name}).insert(
            ignore_permissions=True
        )
    return name


def make_saved_reply_with_actions(title, actions, scope="Global"):
    doc = frappe.get_doc(
        {
            "doctype": "HD Saved Reply",
            "title": title,
            "message": "Hello",
            "scope": scope,
            "actions": actions,
        }
    )
    doc.insert(ignore_permissions=True)
    return doc


class TestHDSavedReplyActions(IntegrationTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        make_agent(AGENT)
        frappe.get_doc("User", AGENT).add_roles("Agent")
        make_team(TEAM, [AGENT])
        make_ticket_type(TICKET_TYPE)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # The team's assignment rule is rolled back, its cached name is not
        clear_doctype_map("Assignment Rule")

    def setUp(self):
        frappe.set_user("Administrator")
        frappe.db.delete("HD Saved Reply")

    def tearDown(self):
        frappe.set_user("Administrator")

    def test_valid_actions_are_saved(self):
        reply = make_saved_reply_with_actions(
            "Valid Actions",
            [
                {"action_type": "Set Status", "value": "Resolved"},
                {"action_type": "Set Priority", "value": "High"},
                {"action_type": "Set Team", "value": TEAM},
                {"action_type": "Assign Agent", "value": AGENT},
            ],
        )
        self.assertEqual(len(json.loads(reply.actions)), 4)

    def test_invalid_action_value_rejected(self):
        with self.assertRaises(frappe.ValidationError):
            make_saved_reply_with_actions(
                "Bad Value",
                [{"action_type": "Set Status", "value": "Nonexistent Status"}],
            )
        # A crafted filter would be unhashable, so it must not reach the keys
        with self.assertRaises(frappe.ValidationError):
            make_saved_reply_with_actions(
                "Crafted Value",
                [{"action_type": "Set Status", "value": ["!=", ""]}],
            )

    def test_duplicate_action_type_rejected(self):
        with self.assertRaises(frappe.ValidationError):
            make_saved_reply_with_actions(
                "Duplicate Actions",
                [
                    {"action_type": "Set Status", "value": "Resolved"},
                    {"action_type": "Set Status", "value": "Closed"},
                ],
            )

    def test_stale_action_does_not_block_unrelated_edits(self):
        """A target deleted after the reply was saved must not wedge the doc."""
        status = make_status("Temporary Status")
        reply = make_saved_reply_with_actions(
            "Stale Action", [{"action_type": "Set Status", "value": status.name}]
        )
        frappe.delete_doc("HD Ticket Status", status.name, force=True)

        reply.reload()
        reply.message = "Edited message"
        reply.save(ignore_permissions=True)
        self.assertEqual(reply.message, "Edited message")

    def test_rendered_saved_reply_includes_only_valid_actions(self):
        status = make_status("Another Temporary Status")
        reply = make_saved_reply_with_actions(
            "With Actions",
            [
                {"action_type": "Set Status", "value": status.name},
                {"action_type": "Assign Agent", "value": AGENT},
            ],
        )
        ticket = make_ticket()
        frappe.delete_doc("HD Ticket Status", status.name, force=True)

        frappe.set_user(AGENT)
        rendered = get_rendered_saved_reply(
            ticket_id=ticket.name, saved_reply_id=reply.name
        )
        self.assertEqual(rendered["message"], "Hello")
        agent_name = frappe.db.get_value("HD Agent", AGENT, "agent_name")
        self.assertEqual(
            rendered["actions"],
            [{"action_type": "Assign Agent", "value": AGENT, "label": agent_name}],
        )

    def test_rendered_saved_reply_respects_permissions(self):
        reply = make_saved_reply_with_actions("Private Reply", [], scope="Personal")
        ticket = make_ticket()

        frappe.set_user(AGENT)
        with self.assertRaises(frappe.PermissionError):
            get_rendered_saved_reply(ticket_id=ticket.name, saved_reply_id=reply.name)

    def test_apply_actions_updates_ticket(self):
        ticket = make_ticket(subject="Apply Actions Ticket")
        note = "Escalated via macro. " * 10  # > 140 chars, needs Small Text

        frappe.set_user(AGENT)
        result = apply_saved_reply_actions(
            ticket_id=ticket.name,
            actions=[
                {"action_type": "Set Status", "value": "Resolved"},
                {"action_type": "Set Priority", "value": "High"},
                {"action_type": "Set Team", "value": TEAM},
                {"action_type": "Set Ticket Type", "value": TICKET_TYPE},
                {"action_type": "Assign Agent", "value": AGENT},
                {"action_type": "Add Comment", "value": note},
            ],
        )

        self.assertEqual(len(result["applied"]), 6)
        self.assertEqual(result["skipped"], [])
        ticket.reload()
        self.assertEqual(ticket.status, "Resolved")
        self.assertEqual(ticket.priority, "High")
        self.assertEqual(ticket.agent_group, TEAM)
        self.assertEqual(ticket.ticket_type, TICKET_TYPE)
        self.assertIn(AGENT, frappe.parse_json(ticket._assign or "[]"))
        self.assertTrue(
            frappe.db.exists(
                "HD Ticket Comment",
                {"reference_ticket": ticket.name, "content": note},
            )
        )

    def test_assign_to_me_action(self):
        ticket = make_ticket(subject="No Value Actions Ticket")

        frappe.set_user(AGENT)
        apply_saved_reply_actions(
            ticket_id=ticket.name,
            actions=[{"action_type": "Assign to Me", "value": ""}],
        )
        ticket.reload()
        self.assertIn(AGENT, frappe.parse_json(ticket._assign or "[]"))

    def test_assignment_actions_mutually_exclusive(self):
        with self.assertRaises(frappe.ValidationError):
            make_saved_reply_with_actions(
                "Conflicting Assignment",
                [
                    {"action_type": "Assign Agent", "value": AGENT},
                    {"action_type": "Assign to Me", "value": ""},
                ],
            )

    def test_apply_actions_skips_invalid_actions(self):
        """Stale or crafted actions are skipped, valid ones still apply."""
        ticket = make_ticket(subject="Skip Invalid Ticket")
        original_status = ticket.status

        frappe.set_user(AGENT)
        result = apply_saved_reply_actions(
            ticket_id=ticket.name,
            actions=[
                {"action_type": "Set Status", "value": "Nope"},
                {"action_type": "Set Priority", "value": ["!=", ""]},
                {"action_type": "Set Team", "value": TEAM},
                # Shadowed by the row above, so it is reported as skipped
                {"action_type": "Set Team", "value": TEAM},
            ],
        )

        self.assertEqual(len(result["skipped"]), 3)
        self.assertEqual(len(result["applied"]), 1)
        ticket.reload()
        self.assertEqual(ticket.status, original_status)
        self.assertEqual(ticket.agent_group, TEAM)

    def test_apply_actions_rejects_malformed_payload(self):
        ticket = make_ticket(subject="Malformed Payload Ticket")

        frappe.set_user(AGENT)
        with self.assertRaises(frappe.ValidationError):
            apply_saved_reply_actions(
                ticket_id=ticket.name, actions='{"action_type": "Set Status"}'
            )

    def test_apply_actions_skips_inactive_agent(self):
        inactive = make_agent("inactive_saved_reply_agent@test.com")
        frappe.db.set_value("HD Agent", inactive, "is_active", 0)
        ticket = make_ticket(subject="Inactive Agent Ticket")

        frappe.set_user(AGENT)
        result = apply_saved_reply_actions(
            ticket_id=ticket.name,
            actions=[{"action_type": "Assign Agent", "value": inactive}],
        )

        self.assertEqual(len(result["skipped"]), 1)
        ticket.reload()
        self.assertNotIn(inactive, frappe.parse_json(ticket._assign or "[]"))

    def test_multiple_tag_actions_allowed(self):
        reply = make_saved_reply_with_actions(
            "Tag Actions",
            [
                {"action_type": "Add Tag", "value": "billing"},
                {"action_type": "Add Tag", "value": "escalated"},
                {"action_type": "Remove Tag", "value": "new"},
            ],
        )
        self.assertEqual(len(json.loads(reply.actions)), 3)

        with self.assertRaises(frappe.ValidationError):
            make_saved_reply_with_actions(
                "Duplicate Tag",
                [
                    {"action_type": "Add Tag", "value": "billing"},
                    {"action_type": "Add Tag", "value": "billing"},
                ],
            )

    def test_tag_add_and_remove_conflict_rejected(self):
        with self.assertRaises(frappe.ValidationError):
            make_saved_reply_with_actions(
                "Conflicting Tags",
                [
                    {"action_type": "Add Tag", "value": "billing"},
                    {"action_type": "Remove Tag", "value": "billing"},
                ],
            )

    def test_tag_with_comma_rejected(self):
        with self.assertRaises(frappe.ValidationError):
            make_saved_reply_with_actions(
                "Comma Tag", [{"action_type": "Add Tag", "value": "a,b"}]
            )

    def test_apply_tag_actions(self):
        ticket = make_ticket(subject="Tag Apply Ticket")
        ticket.add_tag("stale-tag")

        frappe.set_user(AGENT)
        result = apply_saved_reply_actions(
            ticket_id=ticket.name,
            actions=[
                {"action_type": "Add Tag", "value": "macro-tag"},
                {"action_type": "Remove Tag", "value": "stale-tag"},
            ],
        )

        self.assertEqual(len(result["applied"]), 2)
        tags = frappe.db.get_value("HD Ticket", ticket.name, "_user_tags") or ""
        self.assertIn("macro-tag", tags)
        self.assertNotIn("stale-tag", tags)

    def test_apply_actions_accepts_json_string(self):
        ticket = make_ticket(subject="JSON Actions Ticket")

        frappe.set_user(AGENT)
        result = apply_saved_reply_actions(
            ticket_id=ticket.name,
            actions='[{"action_type": "Set Priority", "value": "Low"}]',
        )

        self.assertEqual(len(result["applied"]), 1)
        ticket.reload()
        self.assertEqual(ticket.priority, "Low")
