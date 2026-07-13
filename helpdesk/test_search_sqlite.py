import sqlite3
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from helpdesk.search_sqlite import HelpdeskSearch

EMPTY_FILTER_OPTIONS = {
    "teams": {},
    "statuses": {},
    "priorities": {},
    "customers": {},
    "doctypes": {},
}


class TestHelpdeskSearch(FrappeTestCase):
    def setUp(self):
        self.search = HelpdeskSearch(
            db_name=f"test_helpdesk_search_{frappe.generate_hash(length=8)}.db"
        )
        self.search.drop_index()
        self.search._ensure_fts_table()
        self.addCleanup(self.search.drop_index)

    def index_documents(self, *documents):
        self.search._index_documents(
            [
                {
                    "title": "",
                    "content": "searchable content",
                    **document,
                }
                for document in documents
            ]
        )

    def test_filter_options_supports_access_lists_over_variable_limit(self):
        accessible_ticket = "HD-TICKET-ACCESSIBLE"
        inaccessible_ticket = "HD-TICKET-INACCESSIBLE"
        self.index_documents(
            {
                "doctype": "HD Ticket",
                "name": accessible_ticket,
                "title": "Accessible ticket",
                "reference_ticket": accessible_ticket,
                "agent_group": "Support",
                "status": "Open",
                "priority": "High",
                "customer": "Acme",
            },
            {
                "doctype": "HD Ticket Comment",
                "name": "HD-COMMENT-ACCESSIBLE",
                "reference_ticket": accessible_ticket,
            },
            {
                "doctype": "Communication",
                "name": "HD-COMMUNICATION-ACCESSIBLE",
                "reference_doctype": "HD Ticket",
                "reference_name": accessible_ticket,
            },
            {
                "doctype": "HD Ticket",
                "name": inaccessible_ticket,
                "title": "Inaccessible ticket",
                "reference_ticket": inaccessible_ticket,
                "agent_group": "Restricted",
                "status": "Closed",
                "priority": "Low",
                "customer": "Private",
            },
        )
        accessible_tickets = [
            accessible_ticket,
            "value') OR 1=1 --",
            "日本語-value",
            *(f"HD-TICKET-MISSING-{index}" for index in range(331)),
        ]
        get_connection = self.search._get_connection

        def get_limited_connection(read_only=False):
            connection = get_connection(read_only)
            connection.setlimit(sqlite3.SQLITE_LIMIT_VARIABLE_NUMBER, 999)
            return connection

        with (
            patch.object(
                self.search,
                "_get_accessible_tickets",
                return_value=accessible_tickets,
            ),
            patch.object(
                self.search,
                "_get_connection",
                side_effect=get_limited_connection,
            ),
        ):
            options = self.search.get_filter_options()

        self.assertEqual(
            options,
            {
                "teams": {"Support": 1},
                "statuses": {"Open": 1},
                "priorities": {"High": 1},
                "customers": {"Acme": 1},
                "doctypes": {
                    "HD Ticket": 1,
                    "HD Ticket Comment": 1,
                    "Communication": 1,
                },
            },
        )

    def test_filter_options_handles_duplicate_and_special_ticket_names(self):
        ticket = "HD-TÍCKET-'quoted' 日本語"
        self.index_documents(
            {
                "doctype": "HD Ticket",
                "name": ticket,
                "title": "International ticket",
                "reference_ticket": ticket,
                "agent_group": "International",
                "status": "Open",
                "priority": "Medium",
                "customer": "Globál",
            }
        )

        with patch.object(
            self.search,
            "_get_accessible_tickets",
            return_value=[ticket, ticket],
        ):
            options = self.search.get_filter_options()

        self.assertEqual(options["teams"], {"International": 1})
        self.assertEqual(options["customers"], {"Globál": 1})
        self.assertEqual(options["doctypes"], {"HD Ticket": 1})

    def test_filter_options_binds_accessible_tickets_once(self):
        accessible_tickets = [f"HD-TICKET-{index}" for index in range(10_000)]

        with (
            patch.object(
                self.search,
                "_get_accessible_tickets",
                return_value=accessible_tickets,
            ),
            patch.object(self.search, "index_exists", return_value=True),
            patch.object(self.search, "sql", return_value=[]) as sql,
        ):
            self.search.get_filter_options()

        query, params = sql.call_args.args[:2]
        self.assertEqual(query.count("?"), 1)
        self.assertEqual(len(params), 1)
        self.assertEqual(frappe.parse_json(params[0]), accessible_tickets)
        self.assertEqual(sql.call_args.kwargs, {"read_only": True})

    def test_filter_options_returns_empty_without_index_or_access(self):
        missing_search = HelpdeskSearch(
            db_name=f"test_helpdesk_missing_{frappe.generate_hash(length=8)}.db"
        )
        missing_search.drop_index()
        self.addCleanup(missing_search.drop_index)
        self.assertEqual(missing_search.get_filter_options(), EMPTY_FILTER_OPTIONS)

        with patch.object(self.search, "_get_accessible_tickets", return_value=[]):
            self.assertEqual(self.search.get_filter_options(), EMPTY_FILTER_OPTIONS)
