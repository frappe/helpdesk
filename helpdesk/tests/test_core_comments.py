"""Tests for the HD Ticket Comment / HD Notification → core migration.

Covers the funnel (mentions, reactions, assignment, reopen), the customer
trust boundary on Comment, the activity rider (Info comments), and the
set-based data patches (idempotency, name preservation, collisions).
"""

import frappe
from frappe.tests.utils import FrappeTestCase

from helpdesk.api.comment import get_reactions, toggle_reaction
from helpdesk.api.tags import update_tags
from helpdesk.helpdesk.doctype.hd_ticket.api import get_one
from helpdesk.overrides import desk_form, realtime
from helpdesk.patches import (
    migrate_hd_notifications_to_notification_log,
    migrate_ticket_activities_to_info_comments,
    migrate_ticket_comments_to_comment,
    repoint_comment_reactions_and_files,
)
from helpdesk.test_utils import create_agent, create_user, make_team, make_ticket

AGENT_ONE = "core-comments-agent-one@example.com"
AGENT_TWO = "core-comments-agent-two@example.com"
AGENT_THREE = "core-comments-agent-three@example.com"
CUSTOMER = "core-comments-customer@example.com"


def mention(email: str) -> str:
    return (
        f'<span class="mention" data-type="mention" data-id="{email}" '
        f'data-label="{email}">@{email}</span>'
    )


def ticket_comments(ticket: str, comment_type: str = "Comment") -> list[str]:
    return frappe.get_list(
        "Comment",
        filters={
            "reference_doctype": "HD Ticket",
            "reference_name": ticket,
            "comment_type": comment_type,
        },
        pluck="name",
    )


def notification_rows(**filters) -> list[dict]:
    return frappe.get_list(
        "Notification Log",
        filters=filters,
        fields=[
            "name",
            "type",
            "document_type",
            "document_name",
            "source_doctype",
            "source_name",
            "app",
            "read",
            "subject",
        ],
    )


class CoreCommentsTestCase(FrappeTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        for email in (AGENT_ONE, AGENT_TWO, AGENT_THREE):
            create_agent(email)
        create_user(CUSTOMER)

    def setUp(self):
        frappe.set_user("Administrator")

    def tearDown(self):
        frappe.set_user("Administrator")

    def make_comment(self, ticket, content: str, author: str = AGENT_ONE):
        frappe.set_user(author)
        before = set(ticket_comments(ticket.name))
        ticket.new_comment(content)
        created = set(ticket_comments(ticket.name)) - before
        return frappe.get_doc("Comment", created.pop())


class TestNotificationFunnel(CoreCommentsTestCase):
    def test_mention_notification_points_at_ticket_and_comment(self):
        """Core owns mentions: one row, referencing the ticket, with the
        comment as source. It is app-scoped for the panel and never emails."""
        ticket = make_ticket()
        emails_before = frappe.db.count("Email Queue")
        comment = self.make_comment(ticket, f"look {mention(AGENT_TWO)}")

        frappe.set_user(AGENT_TWO)
        rows = notification_rows(for_user=AGENT_TWO, source_name=comment.name)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.type, "Mention")
        self.assertEqual(row.document_type, "HD Ticket")
        self.assertEqual(row.document_name, ticket.name)
        self.assertEqual(row.source_doctype, "Comment")
        self.assertEqual(row.app, "helpdesk")
        self.assertEqual(frappe.db.count("Email Queue"), emails_before)

    def test_self_mention_is_suppressed(self):
        ticket = make_ticket()
        comment = self.make_comment(ticket, f"note to self {mention(AGENT_ONE)}")
        self.assertEqual(
            notification_rows(for_user=AGENT_ONE, source_name=comment.name), []
        )

    def test_reaction_notification_updates_in_place(self):
        frappe.db.set_single_value("HD Settings", "enable_comment_reactions", 1)
        ticket = make_ticket()
        comment = self.make_comment(ticket, "react to me")

        frappe.set_user(AGENT_TWO)
        toggle_reaction(comment.name, "👍")
        frappe.set_user(AGENT_ONE)
        rows = notification_rows(for_user=AGENT_ONE, source_name=comment.name)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].type, "Reaction")
        frappe.db.set_value("Notification Log", rows[0].name, "read", 1)

        frappe.set_user(AGENT_THREE)
        toggle_reaction(comment.name, "🎉")
        frappe.set_user(AGENT_ONE)
        rows = notification_rows(for_user=AGENT_ONE, source_name=comment.name)
        self.assertEqual(len(rows), 1, "reaction rolls up into one row")
        self.assertFalse(rows[0].read, "roll-up re-marks the row unread")
        self.assertIn("2 people", rows[0].subject)

    def test_reaction_toggle_off_and_response_shape(self):
        frappe.db.set_single_value("HD Settings", "enable_comment_reactions", 1)
        ticket = make_ticket()
        comment = self.make_comment(ticket, "toggle me")

        frappe.set_user(AGENT_TWO)
        self.assertEqual(toggle_reaction(comment.name, "👍")["action"], "added")
        shape = get_reactions(comment.name)
        self.assertEqual(len(shape), 1)
        self.assertEqual(shape[0]["emoji"], "👍")
        self.assertEqual(shape[0]["count"], 1)
        self.assertTrue(shape[0]["current_user_reacted"])
        self.assertEqual(shape[0]["users"][0]["user"], AGENT_TWO)

        self.assertEqual(toggle_reaction(comment.name, "👍")["action"], "removed")
        self.assertEqual(get_reactions(comment.name), [])

    def test_reaction_rejects_bad_input_and_self_notification(self):
        frappe.db.set_single_value("HD Settings", "enable_comment_reactions", 1)
        ticket = make_ticket()
        comment = self.make_comment(ticket, "my own comment")

        frappe.set_user(AGENT_TWO)
        self.assertRaises(frappe.ValidationError, toggle_reaction, comment.name, "🦄")

        unrelated = frappe.get_doc(
            {
                "doctype": "Comment",
                "comment_type": "Comment",
                "reference_doctype": "User",
                "reference_name": AGENT_ONE,
                "content": "not a ticket comment",
            }
        ).insert(ignore_permissions=True)
        self.assertRaises(frappe.ValidationError, toggle_reaction, unrelated.name, "👍")

        frappe.set_user(AGENT_ONE)
        self.assertEqual(toggle_reaction(comment.name, "👍")["action"], "added")
        self.assertEqual(
            notification_rows(for_user=AGENT_ONE, source_name=comment.name), []
        )

    def test_manual_assignment_notifies_once_with_email(self):
        """Core assign_to's row is the only one: it derives app="helpdesk"
        from the ticket and, with Assignment absent from the skip list,
        emails the agent exactly once."""
        ticket = make_ticket()
        emails_before = frappe.db.count("Email Queue")
        frappe.set_user(AGENT_ONE)
        ticket.assign_agent(AGENT_TWO)

        frappe.set_user(AGENT_TWO)
        rows = notification_rows(
            for_user=AGENT_TWO, type="Assignment", document_name=ticket.name
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].app, "helpdesk")
        self.assertEqual(frappe.db.count("Email Queue"), emails_before + 1)

    def test_reopen_notifies_assignees_with_reopened_type(self):
        ticket = make_ticket()
        frappe.set_user(AGENT_ONE)
        ticket.assign_agent(AGENT_ONE)
        ticket.reload()
        ticket.status = "Resolved"
        ticket.save()

        frappe.set_user(AGENT_TWO)
        ticket.reload()
        ticket.status = "Open"
        ticket.save()

        frappe.set_user(AGENT_ONE)
        rows = notification_rows(
            for_user=AGENT_ONE, type="Ticket Reopened", document_name=ticket.name
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].document_type, "HD Ticket")
        self.assertEqual(rows[0].app, "helpdesk")


class TestCommentTrustBoundary(CoreCommentsTestCase):
    SYSTEM_MANAGER = "core-comments-sysmanager@example.com"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_user(cls.SYSTEM_MANAGER).add_roles("System Manager")

    def test_customer_cannot_read_agent_comments(self):
        ticket = make_ticket(raised_by=CUSTOMER, via_customer_portal=True)
        comment = self.make_comment(ticket, "internal note")

        frappe.set_user(CUSTOMER)
        self.assertFalse(frappe.has_permission("Comment", "read", comment.name))
        with self.assertRaises(frappe.PermissionError):
            frappe.get_list("Comment", filters={"reference_name": ticket.name})
        with self.assertRaises(frappe.PermissionError):
            desk_form.get_docinfo(doctype="HD Ticket", name=ticket.name)
        with self.assertRaises(frappe.PermissionError):
            desk_form.get_activity_timeline("HD Ticket", ticket.name)

    def test_ticket_payload_omits_the_comment_cache(self):
        """Core caches comment and email snippets in `_comments`, which skips
        field-level permission checks. Keep it off the ticket payload."""
        ticket = make_ticket(raised_by=CUSTOMER)
        self.make_comment(ticket, "escalate to legal")
        self.assertNotIn("_comments", get_one(ticket.name))

    def test_agent_reads_comments(self):
        ticket = make_ticket()
        comment = self.make_comment(ticket, "internal note")
        frappe.set_user(AGENT_TWO)
        self.assertTrue(frappe.has_permission("Comment", "read", comment.name))

    def test_customer_cannot_join_own_ticket_room(self):
        """The customer reads their ticket over HTTP, but must not enter the
        doc room where internal comment payloads are pushed."""
        ticket = make_ticket(raised_by=CUSTOMER)
        frappe.set_user(CUSTOMER)
        self.assertTrue(frappe.has_permission("HD Ticket", doc=ticket.name))
        self.assertFalse(realtime.has_permission("HD Ticket", ticket.name))

    def test_agent_can_join_ticket_room(self):
        ticket = make_ticket(raised_by=CUSTOMER)
        frappe.set_user(AGENT_ONE)
        self.assertTrue(realtime.has_permission("HD Ticket", ticket.name))

    def test_system_manager_is_denied_like_core(self):
        """Non-agent System Managers have no doc-level HD Ticket access
        (permission hook), so the room gate matches core and denies too."""
        ticket = make_ticket(raised_by=CUSTOMER)
        frappe.set_user(self.SYSTEM_MANAGER)
        self.assertFalse(frappe.has_permission("HD Ticket", doc=ticket.name))
        self.assertFalse(realtime.has_permission("HD Ticket", ticket.name))

    def test_team_restricted_agent_is_still_denied(self):
        """Agents delegate to core, so team restrictions keep applying."""
        team = make_team("Realtime Gate Team", [AGENT_TWO])
        # rollback restores rows but not the singles cache; restore explicitly
        for field in (
            "restrict_tickets_by_agent_group",
            "do_not_restrict_tickets_without_an_agent_group",
        ):
            self.addCleanup(
                frappe.db.set_single_value,
                "HD Settings",
                field,
                frappe.db.get_single_value("HD Settings", field) or 0,
            )
        frappe.db.set_single_value("HD Settings", "restrict_tickets_by_agent_group", 1)
        frappe.db.set_single_value(
            "HD Settings", "do_not_restrict_tickets_without_an_agent_group", 0
        )
        ticket = make_ticket(raised_by=CUSTOMER, agent_group=team.name)

        frappe.set_user(AGENT_TWO)
        self.assertTrue(realtime.has_permission("HD Ticket", ticket.name))
        frappe.set_user(AGENT_ONE)
        with self.assertRaises(frappe.PermissionError):
            realtime.has_permission("HD Ticket", ticket.name)

    def test_other_doctypes_delegate_to_core(self):
        frappe.set_user("Administrator")
        self.assertTrue(realtime.has_permission("User", "Administrator"))
        frappe.set_user(CUSTOMER)
        with self.assertRaises(frappe.PermissionError):
            realtime.has_permission("User", "Administrator")


class TestActivityRider(CoreCommentsTestCase):
    def test_tag_batch_writes_one_info_comment(self):
        ticket = make_ticket()
        frappe.set_user(AGENT_ONE)
        update_tags(
            "HD Ticket", ticket.name, added=[{"name": "alpha"}, {"name": "beta"}]
        )

        infos = ticket_comments(ticket.name, comment_type="Info")
        self.assertEqual(len(infos), 1)
        content = frappe.db.get_value("Comment", infos[0], "content")
        self.assertIn("added tags alpha, beta", content)
        # tag lines are plain text: no mention markup, so no notifications
        self.assertEqual(len(notification_rows(document_name=infos[0])), 0)

    def test_split_marker_writes_info_comment(self):
        source = make_ticket()
        split = make_ticket(subject="Split off", ticket_split_from=source.name)
        infos = ticket_comments(split.name, comment_type="Info")
        contents = [frappe.db.get_value("Comment", n, "content") for n in infos]
        self.assertTrue(
            any(c.startswith("split the ticket from") for c in contents), contents
        )

    def test_field_change_writes_no_activity_row(self):
        """Field changes leave no activity or Info rows; the history feed
        serves them from Version rows instead."""
        from helpdesk.helpdesk.doctype.hd_ticket.api import get_history

        ticket = make_ticket()
        before = frappe.db.count("HD Ticket Activity", {"ticket": ticket.name})
        info_before = len(ticket_comments(ticket.name, comment_type="Info"))
        ticket.reload()
        ticket.priority = "High"
        # test-mode saves skip Version creation unless asked
        ticket.save(ignore_version=False)
        self.assertEqual(
            frappe.db.count("HD Ticket Activity", {"ticket": ticket.name}), before
        )
        self.assertEqual(
            len(ticket_comments(ticket.name, comment_type="Info")), info_before
        )
        frappe.set_user(AGENT_ONE)
        actions = [h.action for h in get_history(ticket.name)]
        self.assertIn("set priority to High", actions)


class TestMigrationPatches(FrappeTestCase):
    """Seeds legacy rows straight into the tables (the legacy write path is
    gone) and runs the patches over them."""

    SEEDED_COMMENTS = ("lgcy0000c1", "lgcy0000c2", "lgcy0000c9")
    SEEDED_SIDECARS = ("lgcyattach1", "lgcytomb001")
    SEEDED_NOTIFICATIONS = ("lgcynotif1", "lgcynotif2", "lgcynotif3", "lgcynotif4")
    SEEDED_ACTIVITIES = ("lgcyact001", "lgcyact002", "lgcyact003")
    SEEDED_CONTENTS = (
        "collided words",
        "stranger",
        "legacy words",
        "added tags alpha, beta",
        "set status to Closed",
        "automatically closed after 7 days of inactivity",
    )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_agent(AGENT_ONE)
        cls.remove_leftovers()
        cls.ticket = make_ticket()

    @classmethod
    def remove_leftovers(cls):
        """The patches commit, so seeds from previous runs survive on the
        test site; start from a clean slate."""
        seeded_names = [
            *cls.SEEDED_COMMENTS,
            *cls.SEEDED_ACTIVITIES,
            *cls.SEEDED_SIDECARS,
        ]
        frappe.db.delete("HD Ticket Comment", {"name": ["in", cls.SEEDED_COMMENTS]})
        frappe.db.delete("HD Ticket Comment", {"content": ["in", cls.SEEDED_CONTENTS]})
        frappe.db.delete("HD Ticket Activity", {"name": ["in", cls.SEEDED_ACTIVITIES]})
        frappe.db.delete("HD Notification", {"name": ["in", cls.SEEDED_NOTIFICATIONS]})
        frappe.db.delete("Notification Log", {"name": ["in", cls.SEEDED_NOTIFICATIONS]})
        frappe.db.delete("Comment", {"name": ["in", seeded_names]})
        frappe.db.delete("Comment", {"content": ["in", cls.SEEDED_CONTENTS]})
        frappe.db.delete("HD Comment Reaction", {"user": AGENT_ONE})

    def seed_legacy_comment(self, name: str, content: str = "legacy words") -> None:
        if frappe.db.exists("HD Ticket Comment", name):
            return
        doc = frappe.new_doc("HD Ticket Comment")
        doc.name = name
        doc.reference_ticket = self.ticket.name
        doc.commented_by = AGENT_ONE
        doc.content = content
        doc.db_insert()

    def seed_legacy_notification(self, name: str, **values) -> None:
        if frappe.db.exists("HD Notification", name):
            return
        doc = frappe.new_doc("HD Notification")
        doc.name = name
        doc.update(
            {
                "user_from": AGENT_ONE,
                "user_to": AGENT_ONE,
                "notification_type": "Assignment",
                "reference_ticket": self.ticket.name,
                **values,
            }
        )
        doc.db_insert()

    def seed_sidecar_comment(self, name: str, comment_type: str, target: str) -> None:
        """A core Comment referencing a legacy comment, as File.after_insert
        and frappe.delete_doc write them."""
        if frappe.db.exists("Comment", name):
            return
        doc = frappe.new_doc("Comment")
        doc.name = name
        doc.comment_type = comment_type
        doc.reference_doctype = "HD Ticket Comment"
        doc.reference_name = target
        doc.content = "sidecar"
        doc.db_insert()

    def seed_legacy_activity(self, name: str, action: str) -> None:
        if frappe.db.exists("HD Ticket Activity", name):
            return
        doc = frappe.new_doc("HD Ticket Activity")
        doc.name = name
        doc.ticket = self.ticket.name
        doc.action = action
        doc.db_insert()

    def test_comments_patch_is_idempotent_and_preserves_names(self):
        self.seed_legacy_comment("lgcy0000c1")
        self.seed_legacy_comment("lgcy0000c2")

        migrate_ticket_comments_to_comment.execute()
        first = frappe.db.count("Comment", {"reference_name": self.ticket.name})
        migrate_ticket_comments_to_comment.execute()
        self.assertEqual(
            frappe.db.count("Comment", {"reference_name": self.ticket.name}), first
        )

        migrated = frappe.get_doc("Comment", "lgcy0000c1")
        self.assertEqual(migrated.comment_type, "Comment")
        self.assertEqual(migrated.comment_email, AGENT_ONE)
        self.assertEqual(migrated.reference_name, self.ticket.name)
        legacy_creation = frappe.db.get_value(
            "HD Ticket Comment", "lgcy0000c1", "creation"
        )
        self.assertEqual(migrated.creation, legacy_creation)

    def test_collision_gets_fresh_name_and_relinked_children(self):
        # a stranger already owns this name in tabComment
        stranger = frappe.get_doc(
            {
                "doctype": "Comment",
                "comment_type": "Comment",
                "reference_doctype": "HD Ticket",
                "reference_name": self.ticket.name,
                "content": "stranger",
            }
        ).insert(ignore_permissions=True)
        colliding = stranger.name
        legacy = frappe.new_doc("HD Ticket Comment")
        legacy.name = colliding
        legacy.creation = "2020-01-01 00:00:00"
        legacy.reference_ticket = self.ticket.name
        legacy.commented_by = AGENT_ONE
        legacy.content = "collided words"
        legacy.db_insert()

        # HD Comment Reaction is autoincrement-named; let the DB assign it
        reaction = frappe.new_doc("HD Comment Reaction")
        reaction.parent = colliding
        reaction.parentfield = "reactions"
        reaction.parenttype = "HD Ticket Comment"
        reaction.idx = 1
        reaction.emoji = "👍"
        reaction.user = AGENT_ONE
        reaction.db_insert()
        reaction_name = frappe.db.get_value(
            "HD Comment Reaction", {"parent": colliding, "user": AGENT_ONE}, "name"
        )

        migrate_ticket_comments_to_comment.execute()

        renamed = frappe.get_list(
            "Comment", filters={"content": "collided words"}, pluck="name"
        )
        self.assertEqual(len(renamed), 1)
        self.assertNotEqual(renamed[0], colliding)
        self.assertEqual(
            frappe.db.get_value("HD Comment Reaction", reaction_name, "parent"),
            renamed[0],
        )

        repoint_comment_reactions_and_files.execute()
        self.assertEqual(
            frappe.db.get_value("HD Comment Reaction", reaction_name, "parenttype"),
            "Comment",
        )

    def test_attachment_sidecar_repoints_but_tombstone_does_not(self):
        """frappe stamps a Comment beside every File; the migration must move
        it with the file. Deleted tombstones point at rows no patch recreates."""
        self.seed_legacy_comment("lgcy0000c1")
        self.seed_sidecar_comment("lgcyattach1", "Attachment", "lgcy0000c1")
        self.seed_sidecar_comment("lgcytomb001", "Deleted", "gonelongago")

        migrate_ticket_comments_to_comment.execute()
        repoint_comment_reactions_and_files.execute()

        self.assertEqual(
            frappe.db.get_value("Comment", "lgcyattach1", "reference_doctype"),
            "Comment",
        )
        self.assertEqual(
            frappe.db.get_value("Comment", "lgcytomb001", "reference_doctype"),
            "HD Ticket Comment",
        )

    def test_activity_migration_takes_only_prefixed_rows(self):
        self.seed_legacy_activity("lgcyact001", "added tags alpha, beta")
        self.seed_legacy_activity("lgcyact002", "set status to Closed")
        self.seed_legacy_activity(
            "lgcyact003", "automatically closed after 7 days of inactivity"
        )

        migrate_ticket_activities_to_info_comments.execute()
        migrate_ticket_activities_to_info_comments.execute()

        self.assertTrue(frappe.db.exists("Comment", "lgcyact001"))
        self.assertTrue(frappe.db.exists("Comment", "lgcyact003"))
        self.assertFalse(
            frappe.db.exists("Comment", "lgcyact002"),
            "field changes stay behind; Versions cover them",
        )
        self.assertEqual(
            frappe.db.get_value("Comment", "lgcyact001", "comment_type"), "Info"
        )

    def test_notifications_patch_maps_types_and_references(self):
        self.seed_legacy_comment("lgcy0000c9")
        migrate_ticket_comments_to_comment.execute()
        self.seed_legacy_notification(
            "lgcynotif1", notification_type="Mention", reference_comment="lgcy0000c9"
        )
        self.seed_legacy_notification("lgcynotif2", notification_type="Assignment")
        self.seed_legacy_notification(
            "lgcynotif3",
            notification_type="Reaction",
            reference_comment="lgcy0000c9",
            message="1 person reacted to your comment",
        )
        self.seed_legacy_notification("lgcynotif4", notification_type="Reaction")

        migrate_hd_notifications_to_notification_log.execute()
        migrate_hd_notifications_to_notification_log.execute()

        # every row points at the ticket; comment-borne ones carry the source
        expectations = {
            "lgcynotif1": ("Mention", "lgcy0000c9"),
            "lgcynotif2": ("Assignment", None),
            "lgcynotif3": ("Reaction", "lgcy0000c9"),
            "lgcynotif4": ("Ticket Reopened", None),
        }
        for name, (ntype, source) in expectations.items():
            row = frappe.db.get_value(
                "Notification Log",
                name,
                [
                    "type",
                    "document_type",
                    "document_name",
                    "source_doctype",
                    "source_name",
                    "app",
                    "subject",
                ],
                as_dict=True,
            )
            self.assertIsNotNone(row, name)
            self.assertEqual(row.type, ntype, name)
            self.assertEqual(row.document_type, "HD Ticket", name)
            self.assertEqual(row.document_name, self.ticket.name, name)
            self.assertEqual(row.source_doctype, "Comment" if source else None, name)
            self.assertEqual(row.source_name, source, name)
            self.assertEqual(row.app, "helpdesk", name)
        self.assertIn(
            "1 person reacted",
            frappe.db.get_value("Notification Log", "lgcynotif3", "subject"),
        )
