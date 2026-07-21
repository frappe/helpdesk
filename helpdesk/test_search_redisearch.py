# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

"""Integration tests for the RediSearch ticket backend.

Mock-free: exercises the real RediSearch module in the cache Redis and the real
HD Ticket permission stack. Skips itself when the RediSearch module is absent.
"""

import frappe
from frappe.tests.utils import FrappeTestCase

from helpdesk.search_redisearch import HelpdeskRediSearch, is_search_module_loaded
from helpdesk.test_utils import add_comment, make_team, make_ticket


class TestHelpdeskRediSearch(FrappeTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not is_search_module_loaded():
            raise cls.skipTest(cls, "RediSearch module not loaded in cache Redis")

        cls._prev_backend = frappe.db.get_single_value("HD Settings", "search_backend")
        frappe.db.set_single_value("HD Settings", "search_backend", "RediSearch")

        cls.ticket_open = make_ticket(
            subject="Login page is broken",
            description="Users cannot log in to the portal",
            status="Open",
            priority="Low",
        )
        cls.ticket_closed = make_ticket(
            subject="Payment gateway timeout",
            description="Card payments fail intermittently",
            priority="High",
        )
        # New tickets are forced to "Open" by the controller; set the closed
        # status directly so the DB-sourced facets have a Closed ticket to count.
        frappe.db.set_value("HD Ticket", cls.ticket_closed.name, "status", "Closed")
        add_comment(cls.ticket_open.name, "investigating the login issue")

        cls.search = HelpdeskRediSearch()
        cls.search.build_index()

    @classmethod
    def tearDownClass(cls):
        cls.search.drop_index()
        frappe.db.set_single_value("HD Settings", "search_backend", cls._prev_backend)
        super().tearDownClass()

    def test_index_exists_after_build(self):
        self.assertTrue(self.search.index_exists())

    def test_search_returns_matching_ticket(self):
        result = self.search.search("login")
        self.assertIn("results", result)
        self.assertIn("summary", result)
        names = {r["name"] for r in result["results"] if r["doctype"] == "HD Ticket"}
        self.assertIn(self.ticket_open.name, names)
        self.assertNotIn(self.ticket_closed.name, names)

    def test_search_result_shape_matches_sqlite(self):
        result = self.search.search("payment")
        self.assertTrue(result["results"])
        row = result["results"][0]
        for key in ("id", "score", "title", "content", "doctype", "name", "author"):
            self.assertIn(key, row)
        # internal permission helper must not leak into the payload
        self.assertNotIn("_ticket", row)

    def test_get_filter_options_counts(self):
        facets = self.search.get_filter_options()
        self.assertEqual(
            set(facets),
            {"teams", "statuses", "priorities", "customers", "doctypes"},
        )
        self.assertGreaterEqual(facets["statuses"].get("Open", 0), 1)
        self.assertGreaterEqual(facets["statuses"].get("Closed", 0), 1)
        self.assertGreaterEqual(facets["priorities"].get("High", 0), 1)
        # doctypes facet is DB-aggregated from HD Ticket under real permission
        self.assertGreaterEqual(facets["doctypes"].get("HD Ticket", 0), 2)

    def test_search_honours_limit(self):
        """A caller ``limit`` caps the returned page (the API forwards it)."""
        result = self.search.search("payment", limit=1)
        self.assertLessEqual(len(result["results"]), 1)

    def test_summary_counts_are_post_permission(self):
        """total/returned/filtered are the post-permission count, never a raw
        pre-permission total that would leak restricted matches."""
        result = self.search.search("login")
        n = len(result["results"])
        self.assertEqual(result["summary"]["total_matches"], n)
        self.assertEqual(result["summary"]["returned_matches"], n)
        self.assertEqual(result["summary"]["filtered_matches"], n)

    def test_empty_query_returns_nothing(self):
        for q in ("", "   ", "!!"):
            result = self.search.search(q)
            self.assertEqual(result["results"], [])
            self.assertEqual(result["summary"]["total_matches"], 0)

    def test_tag_filter_matches_spaced_value(self):
        """A tag filter value containing spaces (a team name) must still match."""
        make_team("Spaced Team Alpha")
        ticket = make_ticket(
            subject="Spaced team routing case",
            description="handled by a team whose name has spaces",
            status="Open",
        )
        frappe.db.set_value(
            "HD Ticket", ticket.name, "agent_group", "Spaced Team Alpha"
        )
        self.search.index_doc("HD Ticket", ticket.name)

        result = self.search.search(
            "routing", filters={"agent_group": "Spaced Team Alpha"}
        )
        names = {r["name"] for r in result["results"] if r["doctype"] == "HD Ticket"}
        self.assertIn(ticket.name, names)

    def test_tag_filter_matches_comma_value(self):
        """A tag value containing a comma must be stored as one tag (not split on
        the default separator) so its filter still matches."""
        from helpdesk.test_utils import create_customer

        create_customer("Acme, Inc")
        ticket = make_ticket(
            subject="Comma customer billing case",
            description="raised by a customer whose name has a comma",
            status="Open",
        )
        frappe.db.set_value("HD Ticket", ticket.name, "customer", "Acme, Inc")
        self.search.index_doc("HD Ticket", ticket.name)

        result = self.search.search("billing", filters={"customer": "Acme, Inc"})
        names = {r["name"] for r in result["results"] if r["doctype"] == "HD Ticket"}
        self.assertIn(ticket.name, names)

    def test_remove_doc_drops_from_index(self):
        ticket = make_ticket(subject="Ephemeral crash report", status="Open")
        self.search.index_doc("HD Ticket", ticket.name)
        self.assertTrue(self.search.search("ephemeral")["results"])
        self.search.remove_doc("HD Ticket", ticket.name)
        names = {r["name"] for r in self.search.search("ephemeral")["results"]}
        self.assertNotIn(ticket.name, names)

    def test_sqlite_backend_still_works_end_to_end(self):
        """Regression: the SQLite backend keeps working when it is selected."""
        frappe.db.set_single_value("HD Settings", "search_backend", "SQLite")
        try:
            from helpdesk.search_sqlite import HelpdeskSearch

            sqlite = HelpdeskSearch()
            self.assertTrue(sqlite.is_search_enabled())
            sqlite.build_index()
            self.assertTrue(sqlite.index_exists())
            names = {
                r["name"]
                for r in sqlite.search("login")["results"]
                if r["doctype"] == "HD Ticket"
            }
            self.assertIn(self.ticket_open.name, names)
            self.assertGreaterEqual(
                sqlite.get_filter_options()["statuses"].get("Open", 0), 1
            )
            # SQLite honours the same limit contract as RediSearch.
            self.assertLessEqual(len(sqlite.search("login", limit=1)["results"]), 1)
        finally:
            frappe.db.set_single_value("HD Settings", "search_backend", "RediSearch")

    def test_toggle_routes_backend(self):
        from helpdesk.api.search import _get_backend

        frappe.db.set_single_value("HD Settings", "search_backend", "RediSearch")
        self.assertIsInstance(_get_backend(), HelpdeskRediSearch)

        from helpdesk.search_sqlite import HelpdeskSearch

        frappe.db.set_single_value("HD Settings", "search_backend", "SQLite")
        self.assertIsInstance(_get_backend(), HelpdeskSearch)
        # restore RediSearch for the rest of the suite
        frappe.db.set_single_value("HD Settings", "search_backend", "RediSearch")

    def test_sqlite_class_disabled_under_redisearch(self):
        from helpdesk.search_sqlite import HelpdeskSearch

        frappe.db.set_single_value("HD Settings", "search_backend", "RediSearch")
        self.assertFalse(HelpdeskSearch().is_search_enabled())
        frappe.db.set_single_value("HD Settings", "search_backend", "SQLite")
        self.assertTrue(HelpdeskSearch().is_search_enabled())
        frappe.db.set_single_value("HD Settings", "search_backend", "RediSearch")
