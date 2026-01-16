# Copyright (c) 2022, Frappe Technologies and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

# Test user emails
AGENT1 = "saved_reply_agent1@test.com"
AGENT2 = "saved_reply_agent2@test.com"
ADMIN_AGENT = "saved_reply_admin@test.com"

# Test team names
TEAM_A = "Test Team A"
TEAM_B = "Test Team B"


def make_user(email, first_name, roles=None):
    """Create a test user."""
    if frappe.db.exists("User", email):
        return frappe.get_doc("User", email)

    user = frappe.get_doc(
        {
            "doctype": "User",
            "email": email,
            "first_name": first_name,
            "send_welcome_email": 0,
        }
    )
    user.insert(ignore_permissions=True)

    if roles:
        for role in roles:
            user.add_roles(role)

    return user


def make_agent(user_email):
    """Create an HD Agent for the given user."""
    if frappe.db.exists("HD Agent", {"user": user_email}):
        return frappe.get_doc("HD Agent", {"user": user_email})

    agent = frappe.get_doc({"doctype": "HD Agent", "user": user_email})
    agent.insert(ignore_permissions=True)
    return agent


def make_team(team_name, members=None):
    """Create an HD Team with optional members."""
    if frappe.db.exists("HD Team", team_name):
        # Delete existing team members
        frappe.db.delete("HD Team Member", {"parent": team_name})
        # Add new members directly to DB
        if members:
            for idx, member in enumerate(members):
                frappe.get_doc(
                    {
                        "doctype": "HD Team Member",
                        "parent": team_name,
                        "parenttype": "HD Team",
                        "parentfield": "users",
                        "user": member,
                        "idx": idx + 1,
                    }
                ).db_insert()
        return frappe.get_doc("HD Team", team_name)

    # Create new team - this will trigger after_insert which creates assignment rule
    team = frappe.get_doc(
        {
            "doctype": "HD Team",
            "team_name": team_name,
            "users": [{"user": m} for m in (members or [])],
        }
    )
    team.insert(ignore_permissions=True)
    return team


def make_saved_reply(title, message, scope="Global", teams=None, owner=ADMIN_AGENT):
    """Create an HD Saved Reply."""
    doc = frappe.get_doc(
        {
            "doctype": "HD Saved Reply",
            "title": title,
            "message": message,
            "scope": scope,
            "teams": [{"team": t} for t in (teams or [])],
        }
    )
    doc.insert(ignore_permissions=True)

    frappe.db.set_value("HD Saved Reply", doc.name, "owner", owner)
    doc.reload()
    return doc


def set_hd_settings(
    restrict_tickets_by_agent_group=None, disable_saved_replies_global_scope=None
):
    """Update HD Settings."""
    if restrict_tickets_by_agent_group is not None:
        frappe.db.set_single_value(
            "HD Settings",
            "restrict_tickets_by_agent_group",
            restrict_tickets_by_agent_group,
        )
    if disable_saved_replies_global_scope is not None:
        frappe.db.set_single_value(
            "HD Settings",
            "disable_saved_replies_global_scope",
            disable_saved_replies_global_scope,
        )


class TestHDSavedReply(IntegrationTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create test users
        make_user(AGENT1, "Agent One", ["Agent"])
        make_user(AGENT2, "Agent Two", ["Agent"])
        make_user(
            ADMIN_AGENT, "Admin Agent", ["Agent", "Agent Manager", "System Manager"]
        )

        # Create HD Agents
        make_agent(AGENT1)
        make_agent(AGENT2)
        make_agent(ADMIN_AGENT)

        # Create teams
        make_team(TEAM_A, [AGENT1])
        make_team(TEAM_B, [AGENT2])

    def setUp(self):
        # Clean up saved replies before each test
        frappe.db.delete("HD Saved Reply")
        # Reset settings to default
        set_hd_settings(
            restrict_tickets_by_agent_group=0, disable_saved_replies_global_scope=0
        )

    # ==========================================================================
    # SCOPE VISIBILITY TESTS
    # ==========================================================================

    def test_global_scope_visible_to_all_agents(self):
        """Global scope saved reply should be visible to all agents."""
        reply = make_saved_reply("Global Reply", "Test message", scope="Global")

        # Test with AGENT1
        frappe.set_user(AGENT1)
        self.assertTrue(frappe.has_permission("HD Saved Reply", doc=reply))

        # Test with AGENT2
        frappe.set_user(AGENT2)
        self.assertTrue(frappe.has_permission("HD Saved Reply", doc=reply))

    def test_global_scope_disabled_not_visible(self):
        """Global scope should be hidden when disable_saved_replies_global_scope is enabled."""
        set_hd_settings(disable_saved_replies_global_scope=1)
        reply = make_saved_reply("Global Reply", "Test message", scope="Global")

        # Agents should NOT have permission (unless owner or admin)
        frappe.set_user(AGENT1)
        self.assertFalse(frappe.has_permission("HD Saved Reply", doc=reply))

        frappe.set_user(AGENT2)
        self.assertFalse(frappe.has_permission("HD Saved Reply", doc=reply))

    def test_global_scope_visible_to_owner_when_disabled(self):
        """Owner should still see global scope reply even when global scope is disabled."""
        set_hd_settings(disable_saved_replies_global_scope=1)
        reply = make_saved_reply(
            "Global Reply", "Test message", scope="Global", owner=AGENT1
        )

        # Owner should have permission
        frappe.set_user(AGENT1)
        self.assertTrue(frappe.has_permission("HD Saved Reply", doc=reply))

        # Non-owner should NOT have permission
        frappe.set_user(AGENT2)
        self.assertFalse(frappe.has_permission("HD Saved Reply", doc=reply))

    def test_personal_scope_visible_to_owner(self):
        """Personal scope saved reply should be visible only to owner."""
        reply = make_saved_reply(
            "Personal Reply", "Test message", scope="Personal", owner=AGENT1
        )

        frappe.set_user(AGENT1)
        self.assertTrue(frappe.has_permission("HD Saved Reply", doc=reply))

    def test_personal_scope_not_visible_to_others(self):
        """Personal scope saved reply should NOT be visible to non-owners."""
        reply = make_saved_reply(
            "Personal Reply", "Test message", scope="Personal", owner=AGENT1
        )

        frappe.set_user(AGENT2)
        self.assertFalse(frappe.has_permission("HD Saved Reply", doc=reply))

    def test_team_scope_visible_to_team_members(self):
        """Team scope saved reply should be visible to team members."""
        set_hd_settings(restrict_tickets_by_agent_group=1)
        reply = make_saved_reply(
            "Team Reply", "Test message", scope="Team", teams=[TEAM_A]
        )

        # Agent1 is in Team A
        frappe.set_user(AGENT1)
        self.assertTrue(frappe.has_permission("HD Saved Reply", doc=reply))

    def test_team_scope_not_visible_without_team_membership(self):
        """Team scope saved reply should NOT be visible to non-team members."""
        set_hd_settings(restrict_tickets_by_agent_group=1)
        reply = make_saved_reply(
            "Team Reply", "Test message", scope="Team", teams=[TEAM_A]
        )

        # Agent2 is in Team B, not Team A
        frappe.set_user(AGENT2)
        self.assertFalse(frappe.has_permission("HD Saved Reply", doc=reply))

    def test_team_scope_visible_when_restriction_disabled(self):
        """Team scope should be visible to all when team restriction is disabled."""
        set_hd_settings(restrict_tickets_by_agent_group=0)
        reply = make_saved_reply(
            "Team Reply", "Test message", scope="Team", teams=[TEAM_A]
        )

        # Even Agent2 (not in Team A) should see it
        frappe.set_user(AGENT2)
        self.assertTrue(frappe.has_permission("HD Saved Reply", doc=reply))

    # ==========================================================================
    # HAS_PERMISSION TESTS
    # ==========================================================================

    def test_owner_has_permission(self):
        """Owner should always have permission to their saved reply."""
        reply = make_saved_reply(
            "My Reply", "Test message", scope="Personal", owner=AGENT1
        )

        frappe.set_user(AGENT1)
        self.assertTrue(frappe.has_permission("HD Saved Reply", doc=reply))

    def test_system_manager_and_agent_manager_has_permission(self):
        """System Manager and Agent Manager should have permission to any saved reply."""
        reply = make_saved_reply(
            "Some Reply", "Test message", scope="Personal", owner=AGENT1
        )

        # Admin (System Manager) should have access
        frappe.set_user(ADMIN_AGENT)
        self.assertTrue(frappe.has_permission("HD Saved Reply", doc=reply))

    def test_team_permission_with_restriction_enabled(self):
        """Team scope should check team membership when restriction is enabled."""
        set_hd_settings(restrict_tickets_by_agent_group=1)
        reply = make_saved_reply(
            "Team A Reply", "Test message", scope="Team", teams=[TEAM_A]
        )

        # Agent1 is in Team A - should have permission
        frappe.set_user(AGENT1)
        self.assertTrue(frappe.has_permission("HD Saved Reply", doc=reply))

        # Agent2 is in Team B - should NOT have permission
        frappe.set_user(AGENT2)
        self.assertFalse(frappe.has_permission("HD Saved Reply", doc=reply))

    def test_team_permission_with_multiple_teams(self):
        """Reply with multiple teams should be visible to members of any team."""
        set_hd_settings(restrict_tickets_by_agent_group=1)
        reply = make_saved_reply(
            "Multi-Team Reply", "Test message", scope="Team", teams=[TEAM_A, TEAM_B]
        )

        # Agent1 is in Team A - should have permission
        frappe.set_user(AGENT1)
        self.assertTrue(frappe.has_permission("HD Saved Reply", doc=reply))

        # Agent2 is in Team B - should have permission
        frappe.set_user(AGENT2)
        self.assertTrue(frappe.has_permission("HD Saved Reply", doc=reply))

    # ==========================================================================
    # PERMISSION_QUERY TESTS (get_list visibility)
    # ==========================================================================

    def test_admin_sees_all_replies(self):
        """Admin user should see all saved replies in the list."""
        make_saved_reply("Global Reply", "Test", scope="Global")
        make_saved_reply("Personal Reply 1", "Test", scope="Personal", owner=AGENT1)
        make_saved_reply("Personal Reply 2", "Test", scope="Personal", owner=AGENT2)
        make_saved_reply("Team Reply", "Test", scope="Team", teams=[TEAM_A])

        # Admin should see all replies
        frappe.set_user(ADMIN_AGENT)
        replies = frappe.get_list("HD Saved Reply", pluck="name")
        self.assertEqual(len(replies), 4)

    def test_permission_query_includes_global_scope(self):
        """Permission query should include global scope when enabled."""
        set_hd_settings(disable_saved_replies_global_scope=0)
        global_reply = make_saved_reply("Global Reply", "Test", scope="Global")

        frappe.set_user(AGENT1)
        replies = frappe.get_list("HD Saved Reply", pluck="name")
        self.assertIn(global_reply.name, replies)

    def test_permission_query_excludes_global_when_disabled(self):
        """Permission query should exclude global scope when disabled."""
        set_hd_settings(disable_saved_replies_global_scope=1)
        make_saved_reply("Global Reply", "Test", scope="Global")
        personal_reply = make_saved_reply(
            "Personal Reply", "Test", scope="Personal", owner=AGENT1
        )

        frappe.set_user(AGENT1)
        replies = frappe.get_list("HD Saved Reply", pluck="name")
        # Global should not be visible, but personal should
        self.assertIn(personal_reply.name, replies)
        self.assertEqual(len([r for r in replies]), 1)  # Only personal reply visible

    def test_permission_query_includes_personal_scope_for_owner(self):
        """Permission query should include personal scope filtered by owner."""
        personal_reply = make_saved_reply(
            "Personal Reply", "Test", scope="Personal", owner=AGENT1
        )
        make_saved_reply("Agent2 Personal", "Test", scope="Personal", owner=AGENT2)

        frappe.set_user(AGENT1)
        replies = frappe.get_list(
            "HD Saved Reply", filters={"scope": "Personal"}, pluck="name"
        )
        self.assertIn(personal_reply.name, replies)
        self.assertEqual(len(replies), 1)  # Only owner's personal reply

    def test_permission_query_includes_team_scope(self):
        """Permission query should include team scope."""
        set_hd_settings(restrict_tickets_by_agent_group=0)
        team_reply = make_saved_reply(
            "Team Reply", "Test", scope="Team", teams=[TEAM_A]
        )

        frappe.set_user(AGENT1)
        replies = frappe.get_list(
            "HD Saved Reply", filters={"scope": "Team"}, pluck="name"
        )
        self.assertIn(team_reply.name, replies)

    def test_permission_query_team_filter_with_restriction(self):
        """Permission query should filter team scope by membership when restricted."""
        set_hd_settings(restrict_tickets_by_agent_group=1)
        team_a_reply = make_saved_reply(
            "Team A Reply", "Test", scope="Team", teams=[TEAM_A]
        )
        make_saved_reply("Team B Reply", "Test", scope="Team", teams=[TEAM_B])

        frappe.set_user(AGENT1)
        replies = frappe.get_list(
            "HD Saved Reply", filters={"scope": "Team"}, pluck="name"
        )
        # Agent1 is in Team A, should only see Team A reply
        self.assertIn(team_a_reply.name, replies)
        self.assertEqual(len(replies), 1)

    def test_agent_list_filter_personal_replies(self):
        """Agent should only see their own personal replies in list."""
        reply1 = make_saved_reply(
            "Agent1 Personal", "Test", scope="Personal", owner=AGENT1
        )
        make_saved_reply("Agent2 Personal", "Test", scope="Personal", owner=AGENT2)

        frappe.set_user(AGENT1)
        replies = frappe.get_list(
            "HD Saved Reply",
            filters={"scope": "Personal"},
            pluck="name",
        )
        self.assertIn(reply1.name, replies)
        self.assertEqual(len(replies), 1)

    def test_agent_list_filter_team_replies(self):
        """Agent should see team replies for their teams."""
        set_hd_settings(restrict_tickets_by_agent_group=1)
        reply_a = make_saved_reply("Team A Reply", "Test", scope="Team", teams=[TEAM_A])
        make_saved_reply("Team B Reply", "Test", scope="Team", teams=[TEAM_B])

        frappe.set_user(AGENT1)
        replies = frappe.get_list(
            "HD Saved Reply",
            filters={"scope": "Team"},
            pluck="name",
        )
        self.assertIn(reply_a.name, replies)
        self.assertEqual(len(replies), 1)

    def test_agent_list_global_replies(self):
        """Agent should see global replies when enabled."""
        set_hd_settings(disable_saved_replies_global_scope=0)
        reply = make_saved_reply("Global Reply", "Test", scope="Global")

        frappe.set_user(AGENT1)
        replies = frappe.get_list(
            "HD Saved Reply",
            filters={"scope": "Global"},
            pluck="name",
        )
        self.assertIn(reply.name, replies)

    def test_agent_list_no_global_when_disabled(self):
        """Agent should not see global replies when disabled."""
        set_hd_settings(disable_saved_replies_global_scope=1)
        make_saved_reply("Global Reply", "Test", scope="Global")

        frappe.set_user(AGENT1)
        replies = frappe.get_list(
            "HD Saved Reply",
            filters={"scope": "Global"},
            pluck="name",
        )
        self.assertEqual(len(replies), 0)

    # ==========================================================================
    # EDIT PERMISSION TESTS
    # ==========================================================================

    def test_owner_can_edit_reply(self):
        """Owner should be able to edit their saved reply."""
        reply = make_saved_reply(
            "My Reply", "Original message", scope="Personal", owner=AGENT1
        )

        frappe.set_user(AGENT1)
        doc = frappe.get_doc("HD Saved Reply", reply.name)
        doc.message = "Updated message"
        doc.save()  # Should not raise
        self.assertEqual(doc.message, "Updated message")

    def test_admin_can_edit_any_reply(self):
        """Admin should be able to edit any saved reply."""
        reply = make_saved_reply(
            "Agent Reply", "Original message", scope="Personal", owner=AGENT1
        )

        frappe.set_user(ADMIN_AGENT)
        doc = frappe.get_doc("HD Saved Reply", reply.name)
        doc.message = "Admin updated"
        doc.save()  # Should not raise
        self.assertEqual(doc.message, "Admin updated")

    def test_non_owner_cannot_edit_personal_reply(self):
        """Non-owner agent should not be able to edit another's personal reply."""
        reply = make_saved_reply(
            "Agent1 Personal", "Original message", scope="Personal", owner=AGENT1
        )

        frappe.set_user(AGENT2)
        doc = frappe.get_doc("HD Saved Reply", reply.name)
        doc.message = "Agent2 trying to edit"
        with self.assertRaises(frappe.PermissionError):
            doc.save()

    def test_non_team_member_cannot_edit_team_reply(self):
        """Non-team member should not be able to edit team scope reply."""
        set_hd_settings(restrict_tickets_by_agent_group=1)
        reply = make_saved_reply(
            "Team A Reply",
            "Original message",
            scope="Team",
            teams=[TEAM_A],
            owner=AGENT1,
        )

        # Agent2 is in Team B, not Team A
        frappe.set_user(AGENT2)
        doc = frappe.get_doc("HD Saved Reply", reply.name)
        doc.message = "Agent2 trying to edit"
        with self.assertRaises(frappe.PermissionError):
            doc.save()

    # ==========================================================================
    # COMBINED SETTINGS TESTS
    # ==========================================================================

    def test_both_restrictions_enabled(self):
        """Test behavior when both restriction flags are enabled."""
        set_hd_settings(
            restrict_tickets_by_agent_group=1, disable_saved_replies_global_scope=1
        )

        global_reply = make_saved_reply("Global Reply", "Test", scope="Global")
        team_a_reply = make_saved_reply(
            "Team A Reply", "Test", scope="Team", teams=[TEAM_A]
        )
        personal_reply = make_saved_reply(
            "Personal Reply", "Test", scope="Personal", owner=AGENT1
        )

        frappe.set_user(AGENT1)
        # Agent1: should NOT see global (disabled), SHOULD see Team A, SHOULD see personal
        self.assertFalse(frappe.has_permission("HD Saved Reply", doc=global_reply))
        self.assertTrue(frappe.has_permission("HD Saved Reply", doc=team_a_reply))
        self.assertTrue(frappe.has_permission("HD Saved Reply", doc=personal_reply))

        frappe.set_user(AGENT2)
        # Agent2: should NOT see global (disabled), should NOT see Team A (not member)
        self.assertFalse(frappe.has_permission("HD Saved Reply", doc=global_reply))
        self.assertFalse(frappe.has_permission("HD Saved Reply", doc=team_a_reply))

    def test_no_team_membership_with_restriction(self):
        """Agent with no team membership gets limited access when restriction enabled."""
        # Create agent with no team
        no_team_agent = "saved_reply_no_team@test.com"
        make_user(no_team_agent, "No Team Agent", ["Agent"])
        make_agent(no_team_agent)

        set_hd_settings(restrict_tickets_by_agent_group=1)

        team_reply = make_saved_reply(
            "Team Reply", "Test", scope="Team", teams=[TEAM_A]
        )
        global_reply = make_saved_reply("Global Reply", "Test", scope="Global")
        personal_reply = make_saved_reply(
            "Personal Reply", "Test", scope="Personal", owner=no_team_agent
        )

        frappe.set_user(no_team_agent)
        # Agent with no team should NOT see team replies
        self.assertFalse(frappe.has_permission("HD Saved Reply", doc=team_reply))
        # Should see global (if enabled)
        self.assertTrue(frappe.has_permission("HD Saved Reply", doc=global_reply))
        # Should see their own personal
        self.assertTrue(frappe.has_permission("HD Saved Reply", doc=personal_reply))

    # ==========================================================================
    # GET_DOC VISIBILITY TESTS (using permission query)
    # ==========================================================================

    def test_get_doc_global_scope_visible(self):
        """frappe.get_doc should work for global scope reply."""
        reply = make_saved_reply("Global Reply", "Test", scope="Global")

        frappe.set_user(AGENT1)
        doc = frappe.get_doc("HD Saved Reply", reply.name)
        self.assertEqual(doc.title, "Global Reply")

    def test_get_doc_personal_scope_owner(self):
        """Owner should be able to get_doc their personal reply."""
        reply = make_saved_reply(
            "Personal Reply", "Test", scope="Personal", owner=AGENT1
        )

        frappe.set_user(AGENT1)
        doc = frappe.get_doc("HD Saved Reply", reply.name)
        self.assertEqual(doc.title, "Personal Reply")

    def test_get_doc_team_scope_member(self):
        """Team member should be able to get_doc team reply."""
        set_hd_settings(restrict_tickets_by_agent_group=1)
        reply = make_saved_reply("Team Reply", "Test", scope="Team", teams=[TEAM_A])

        frappe.set_user(AGENT1)
        doc = frappe.get_doc("HD Saved Reply", reply.name)
        self.assertEqual(doc.title, "Team Reply")

    def test_get_list_respects_permission_query(self):
        """get_list should respect permission_query filtering."""
        set_hd_settings(restrict_tickets_by_agent_group=1)

        # Create replies with different scopes
        global_reply = make_saved_reply("Global", "Test", scope="Global")
        personal_agent1 = make_saved_reply(
            "Personal A1", "Test", scope="Personal", owner=AGENT1
        )
        personal_agent2 = make_saved_reply(
            "Personal A2", "Test", scope="Personal", owner=AGENT2
        )
        team_a_reply = make_saved_reply("Team A", "Test", scope="Team", teams=[TEAM_A])
        team_b_reply = make_saved_reply("Team B", "Test", scope="Team", teams=[TEAM_B])

        # Agent1 should see: global, their personal, Team A
        frappe.set_user(AGENT1)
        replies = frappe.get_list("HD Saved Reply", pluck="name")
        self.assertIn(global_reply.name, replies)
        self.assertIn(personal_agent1.name, replies)
        self.assertNotIn(personal_agent2.name, replies)
        self.assertIn(team_a_reply.name, replies)
        self.assertNotIn(team_b_reply.name, replies)

    def tearDown(self):
        frappe.set_user("Administrator")
