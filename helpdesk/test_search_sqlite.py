from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from helpdesk.patches import relabel_comment_search_index
from helpdesk.search_sqlite import HelpdeskSearch
from helpdesk.test_utils import create_user, make_ticket

RESTRICTED_USER = "helpdesk-search-user@example.com"


class TestSearchPermissionFilter(FrappeTestCase):
    """Under PREFILTER_LIMIT the permission filter binds exactly; over it,
    _drop_unpermitted gates the results instead."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # HD Customer grants doctype-level read; row visibility still comes from
        # the permission query. A role-less user cannot get_list at all.
        create_user(RESTRICTED_USER).add_roles("HD Customer")
        cls.own_ticket = make_ticket(
            subject="Search perm own", raised_by=RESTRICTED_USER
        )
        cls.other_ticket = make_ticket(subject="Search perm other")

    def tearDown(self):
        frappe.set_user("Administrator")

    def test_small_sites_bind_an_exact_prefilter(self):
        search = HelpdeskSearch()
        filters = search.get_search_filters()

        self.assertIn(self.own_ticket.name, filters["reference_ticket"])
        self.assertFalse(search.is_post_filter_required)

    def test_large_sites_skip_the_prefilter_and_flag_post_filtering(self):
        search = HelpdeskSearch()
        with patch("helpdesk.search_sqlite.PREFILTER_LIMIT", 1):
            filters = search.get_search_filters()

        self.assertEqual(filters, {})
        self.assertTrue(search.is_post_filter_required)

    def test_post_filter_drops_tickets_the_user_cannot_see(self):
        rows = [
            {"reference_ticket": self.own_ticket.name},
            {"reference_ticket": self.other_ticket.name},
            # Communication rows carry the ticket in reference_name only.
            {"reference_ticket": None, "reference_name": self.own_ticket.name},
            # No resolvable ticket: must fail closed.
            {"reference_ticket": None, "reference_name": None},
        ]

        frappe.set_user(RESTRICTED_USER)
        kept = HelpdeskSearch()._drop_unpermitted(rows)

        self.assertEqual(
            [HelpdeskSearch._ticket_of(r) for r in kept],
            [self.own_ticket.name, self.own_ticket.name],
        )

    def test_filter_options_bind_a_constant_number_of_variables(self):
        """Runs the json_each facets query for real."""
        options = HelpdeskSearch().get_filter_options()

        self.assertEqual(
            set(options), {"teams", "statuses", "priorities", "customers", "doctypes"}
        )


class TestSearchIndexRelabel(FrappeTestCase):
    """The patch rewrites the FTS rows in place instead of rebuilding, which
    would cost hours with search down. Runs against a throwaway index so the
    site's real one is never touched."""

    TEST_INDEX = "test_relabel_search.db"

    def setUp(self):
        self.search = HelpdeskSearch(db_name=self.TEST_INDEX)
        self.search.drop_index()
        self.search._ensure_fts_table()
        self.addCleanup(self.search.drop_index)

    def run_patch(self) -> None:
        with patch.object(
            relabel_comment_search_index,
            "HelpdeskSearch",
            lambda: HelpdeskSearch(db_name=self.TEST_INDEX),
        ):
            relabel_comment_search_index.execute()

    def insert_row(self, doc_id: str, doctype: str, name: str, ticket) -> None:
        self.search.sql(
            """INSERT INTO search_fts
                (doc_id, title, content, doctype, name, reference_ticket)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (doc_id, "", "refund promised", doctype, name, ticket),
            commit=True,
        )

    def row(self, name: str) -> dict:
        return self.search.sql(
            """SELECT doc_id, doctype, reference_doctype, reference_name,
                reference_ticket, typeof(reference_ticket) AS ticket_type
            FROM search_fts WHERE name = ?""",
            (name,),
            read_only=True,
        )[0]

    def test_relabel_keeps_rows_searchable_and_leaves_others_alone(self):
        self.insert_row("HD Ticket Comment:abc123", "HD Ticket Comment", "abc123", "42")
        self.insert_row("Communication:mail01", "Communication", "mail01", "42")

        self.run_patch()

        comment = self.row("abc123")
        self.assertEqual(comment["doc_id"], "Comment:abc123")
        self.assertEqual(comment["doctype"], "Comment")
        self.assertEqual(comment["reference_doctype"], "HD Ticket")
        self.assertEqual(comment["reference_name"], "42")
        self.assertEqual(comment["reference_ticket"], "42")

        # the tokenized columns must survive the rewrite, else search silently
        # returns nothing for every migrated comment
        hits = self.search.sql(
            "SELECT doc_id FROM search_fts WHERE search_fts MATCH ?",
            ("refund",),
            read_only=True,
        )
        self.assertIn("Comment:abc123", [hit["doc_id"] for hit in hits])

        self.assertEqual(self.row("mail01")["doctype"], "Communication")

        self.run_patch()
        self.assertEqual(self.row("abc123"), comment)

    def test_integer_ticket_names_are_cast_to_text(self):
        """Autoincrement-era rows stored ticket names as SQLite integers; the
        permission prefilter binds strings and SQLite compares by type, so
        those rows match nothing until they are cast."""
        self.insert_row("HD Ticket:10", "HD Ticket", "10", 10)

        self.run_patch()

        ticket = self.row("10")
        self.assertEqual(ticket["ticket_type"], "text")
        self.assertEqual(ticket["reference_ticket"], "10")
