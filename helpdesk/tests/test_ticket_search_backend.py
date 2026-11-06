from unittest import SkipTest
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.tests.utils import change_settings
from redis.exceptions import ResponseError

from helpdesk.search_redis import RedisSearchBackend
from helpdesk.search_sqlite import HelpdeskSearch
from helpdesk.test_utils import create_agent, create_contact, make_team, make_ticket
from helpdesk.ticket_search import (
    SearchIndexMissingError,
    SQLiteBackend,
    get_search_backend,
    update_doc_index,
)


class TestRedisTicketSearch(IntegrationTestCase):
    def setUp(self):
        try:
            frappe.cache().execute_command("FT._LIST")
        except ResponseError as error:
            if "unknown command" not in str(error).lower():
                raise
            raise SkipTest("Redis Search is required for integration tests") from error
        mute_emails = patch.dict(frappe.flags, {"mute_emails": True})
        mute_emails.start()
        self.addCleanup(mute_emails.stop)
        self.token = "search" + frappe.generate_hash(length=10)
        prefix = patch.object(RedisSearchBackend, "PREFIX", f"{self.token}:")
        prefix.start()
        self.addCleanup(prefix.stop)
        self.backend = RedisSearchBackend()
        self.addCleanup(self.backend.drop_index)
        self.agent = create_agent(f"{self.token}@example.com")
        self.ticket = make_ticket(subject=self.token, description="zebra" + self.token)
        self.backend.build_index()

    def test_agent_search_update_delete_and_rebuild(self):
        with self.set_user(self.agent.name):
            result = self.backend.search(self.token)
        self.assertEqual(result["results"][0]["name"], str(self.ticket.name))
        self.assertEqual(result["summary"]["total_matches"], 1)
        frappe.db.set_value(
            "HD Ticket", self.ticket.name, "subject", "replacement" + self.token
        )
        self.backend.index_doc("HD Ticket", self.ticket.name)
        self.assertEqual(self.backend.search(self.token)["results"], [])
        self.assertEqual(
            len(self.backend.search("replacement" + self.token)["results"]), 1
        )
        frappe.delete_doc("HD Ticket", self.ticket.name, force=True)
        self.backend.remove_doc("HD Ticket", self.ticket.name)
        self.assertEqual(self.backend.search("replacement" + self.token)["results"], [])
        self.backend.build_index(force=True)
        self.assertTrue(self.backend.index_exists())

    def test_team_permission_changes_apply_without_reindexing(self):
        other = create_agent(f"other-{self.token}@example.com")
        team = make_team(self.token, [other.name])
        frappe.db.set_value("HD Ticket", self.ticket.name, "agent_group", team.name)
        self.backend.index_doc("HD Ticket", self.ticket.name)
        with change_settings(
            "HD Settings",
            {
                "restrict_tickets_by_agent_group": 1,
                "do_not_restrict_tickets_without_an_agent_group": 0,
            },
        ):
            with self.set_user(self.agent.name):
                result = self.backend.search(self.token)
                self.assertEqual(result["results"], [])
                self.assertEqual(result["summary"]["total_matches"], 0)
                self.assertNotIn(team.name, self.backend.get_filter_options()["teams"])
            with self.set_user(other.name):
                self.assertEqual(len(self.backend.search(self.token)["results"]), 1)

    def test_title_filters_and_syntax_are_literal(self):
        self.assertEqual(
            self.backend.search("zebra" + self.token, title_only=True)["results"], []
        )
        content_results = self.backend.search("zebra" + self.token)["results"]
        self.assertIn("HD Ticket", {row["doctype"] for row in content_results})
        self.assertIn("Communication", {row["doctype"] for row in content_results})
        result = self.backend.search(
            self.token, filters={"status": [self.ticket.status]}
        )
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(self.backend.search("* | @title:{}")["results"], [])
        self.assertEqual(self.backend.search("")["results"], [])
        with self.assertRaises(frappe.ValidationError):
            self.backend.search(self.token, filters={"arbitrary": ["value"]})

    def test_redis_does_not_open_sqlite(self):
        with patch.object(
            HelpdeskSearch,
            "_get_connection",
            side_effect=AssertionError("SQLite opened"),
        ):
            self.backend.build_index(force=True)
            self.backend.index_doc("HD Ticket", self.ticket.name)
            self.assertEqual(len(self.backend.search(self.token)["results"]), 1)
            self.assertTrue(self.backend.get_filter_options())

    def test_incomplete_build_is_not_marked_ready(self):
        with (
            patch.object(
                self.backend,
                "_write_document",
                side_effect=ResponseError("test write failure"),
            ),
            self.assertRaises(ResponseError),
        ):
            self.backend.build_index(force=True)
        self.assertFalse(self.backend.index_exists())
        with self.assertRaises(SearchIndexMissingError):
            self.backend.search(self.token)
        self.backend.build_index()
        self.assertTrue(self.backend.index_exists())

    def test_distinct_namespace_does_not_expose_other_documents(self):
        with patch.object(RedisSearchBackend, "PREFIX", f"other-{self.token}:"):
            other = RedisSearchBackend()
        self.addCleanup(other.drop_index)
        self.assertNotEqual(other.index, self.backend.index)
        self.assertFalse(other.index_exists())
        with self.assertRaises(SearchIndexMissingError):
            other.search(self.token)
        self.assertEqual(len(self.backend.search(self.token)["results"]), 1)

    def test_customer_cannot_search_internal_comments(self):
        email = f"customer-{self.token}@example.com"
        create_contact(self.token, email)
        ticket = make_ticket(subject=self.token + "portal", raised_by=email)
        comment = ticket.add_comment("Comment", self.token + "private")
        self.backend.index_doc("HD Ticket", ticket.name)
        self.backend.index_doc("Comment", comment.name)
        with self.set_user(self.agent.name):
            self.assertEqual(
                len(self.backend.search(self.token + "private")["results"]), 1
            )
        with self.set_user(email):
            self.assertEqual(self.backend.search(self.token + "private")["results"], [])
            self.assertEqual(
                len(self.backend.search(self.token + "portal")["results"]), 1
            )

    def test_pagination_and_punctuated_team_filter(self):
        team = make_team(self.token + " A,B / ü", [self.agent.name])
        expected = set()
        for index in range(3):
            ticket = make_ticket(
                subject=f"{self.token} pagination {index}", agent_group=team.name
            )
            expected.add(str(ticket.name))
            self.backend.index_doc("HD Ticket", ticket.name)
        with patch.object(self.backend, "PAGE_SIZE", 2):
            with self.set_user(self.agent.name):
                result = self.backend.search(
                    self.token, filters={"agent_group": [team.name]}
                )
                with patch.object(
                    self.backend, "_command", wraps=self.backend._command
                ) as command:
                    options = self.backend.get_filter_options()
        self.assertEqual(len(result["results"]), 3)
        self.assertEqual({row["name"] for row in result["results"]}, expected)
        self.assertEqual(result["summary"]["total_matches"], 3)
        self.assertEqual(options["teams"][team.name], 3)
        aggregate = next(
            call.args
            for call in command.call_args_list
            if call.args[0] == "FT.AGGREGATE"
        )
        for unnecessary in ("@content", "@title", "ADDSCORES", "SORTBY"):
            self.assertNotIn(unnecessary, aggregate)

    def test_deleting_ticket_removes_indexed_comments(self):
        comment = self.ticket.add_comment("Comment", self.token + "child")
        self.backend.index_doc("Comment", comment.name)
        with self.set_user(self.agent.name):
            self.assertEqual(
                len(self.backend.search(self.token + "child")["results"]), 1
            )
        frappe.delete_doc("HD Ticket", self.ticket.name, force=True)
        self.backend.remove_doc("HD Ticket", self.ticket.name)
        self.assertEqual(
            list(
                self.backend._rows("@reference_ticket:{" + str(self.ticket.name) + "}")
            ),
            [],
        )

    def test_prefix_search_returns_safe_html(self):
        frappe.db.set_value(
            "HD Ticket",
            self.ticket.name,
            "subject",
            self.token + " <img src=x onerror=alert(1)>",
        )
        self.backend.index_doc("HD Ticket", self.ticket.name)
        result = self.backend.search(self.token[:-1], title_only=True)
        self.assertEqual(len(result["results"]), 1)
        row = result["results"][0]
        self.assertNotIn("<", row["title"])
        self.assertNotIn("<", row["content"])
        self.assertEqual(row["name"], str(self.ticket.name))

    def test_update_hook_waits_for_commit(self):
        with patch("frappe.enqueue") as enqueue:
            update_doc_index(self.ticket)
        self.assertTrue(enqueue.call_args.kwargs["enqueue_after_commit"])
        self.assertIn("rq_retry", enqueue.call_args.kwargs)
        self.assertNotIn("retry", enqueue.call_args.kwargs)
        self.assertEqual(enqueue.call_args.kwargs["name"], self.ticket.name)


class TestTicketBackendSelection(IntegrationTestCase):
    def test_sqlite_is_default_and_bad_configuration_fails(self):
        with patch.dict(frappe.conf, {}, clear=True):
            self.assertEqual(type(get_search_backend()).__name__, "SQLiteBackend")
        with patch.dict(frappe.conf, {"helpdesk_search_backend": "unknown"}):
            with self.assertRaises(frappe.ValidationError):
                get_search_backend()


class TestSQLiteTicketSearch(IntegrationTestCase):
    def test_default_backend_keeps_search_and_document_updates(self):
        token = "sqlite" + frappe.generate_hash(length=10)
        index_name = patch.object(HelpdeskSearch, "INDEX_NAME", token + ".db")
        index_name.start()
        self.addCleanup(index_name.stop)
        backend = SQLiteBackend()
        self.addCleanup(backend.search_index.drop_index)
        agent = create_agent(f"{token}@example.com")
        ticket = make_ticket(subject=token, description="Initial content")
        backend.build_index()
        with self.set_user(agent.name):
            result = backend.search(token)
        self.assertEqual(result["results"][0]["name"], str(ticket.name))
        frappe.db.set_value("HD Ticket", ticket.name, "subject", "replacement" + token)
        backend.index_doc("HD Ticket", ticket.name)
        self.assertEqual(backend.search(token)["results"], [])
        self.assertEqual(len(backend.search("replacement" + token)["results"]), 1)
        frappe.delete_doc("HD Ticket", ticket.name, force=True)
        backend.remove_doc("HD Ticket", ticket.name)
        self.assertEqual(backend.search("replacement" + token)["results"], [])
