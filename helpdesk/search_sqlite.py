# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

import frappe
from frappe.search.sqlite_search import SQLiteSearch, SQLiteSearchIndexMissingError


class HelpdeskSearchIndexMissingError(SQLiteSearchIndexMissingError):
    pass


# Most tickets to bind as an exact IN (...) prefilter; past this the prefilter is
# skipped and results are permission-checked after the search instead, since an
# unbounded IN list hits SQLite's bound-variable ceiling.
PREFILTER_LIMIT = 500


class HelpdeskSearch(SQLiteSearch):
    INDEX_NAME = "helpdesk_search.db"

    # Resting value: core search() can bail before get_search_filters() runs.
    is_post_filter_required = False

    INDEX_SCHEMA = {
        "metadata_fields": [
            "agent_group",
            "customer",
            "status",
            "priority",
            "owner",
            "reference_doctype",
            "reference_name",
            "reference_ticket",
        ],
        "tokenizer": "unicode61 remove_diacritics 2 tokenchars '-_'",
    }

    INDEXABLE_DOCTYPES = {
        "HD Ticket": {
            "fields": [
                "name",
                {"title": "subject"},
                {"content": "description"},
                "modified",
                "agent_group",
                "status",
                "priority",
                "raised_by",
                "owner",
            ],
        },
        "HD Ticket Comment": {
            "fields": [
                "name",
                "content",
                "modified",
                "reference_ticket",
                "commented_by",
                "owner",
            ],
        },
        "Communication": {
            "fields": [
                "name",
                "content",
                "modified",
                "reference_doctype",
                "reference_name",
                "sender",
                "owner",
            ],
            "filters": {"reference_doctype": "HD Ticket"},
        },
    }

    def search(self, query, title_only: bool = False, filters: dict | None = None):
        result = super().search(query, title_only=title_only, filters=filters)
        if self.is_post_filter_required:
            result["results"] = self._drop_unpermitted(result["results"])
            result["summary"]["filtered_matches"] = len(result["results"])
        return result

    def get_search_filters(self) -> dict:
        """Return permission filters based on accessible tickets."""
        accessible_tickets = self.get_accessible_tickets()
        self.is_post_filter_required = accessible_tickets is None
        if self.is_post_filter_required:
            return {}
        return {"reference_ticket": accessible_tickets}

    def get_accessible_tickets(self) -> list[str] | None:
        """Accessible tickets when few enough to prefilter, else None."""
        tickets = frappe.get_list(
            "HD Ticket", pluck="name", limit_page_length=PREFILTER_LIMIT + 1
        )
        if len(tickets) > PREFILTER_LIMIT:
            return None
        return tickets

    def _drop_unpermitted(self, results: list[dict]) -> list[dict]:
        """Permission gate for the unprefiltered branch: one get_list bounded by
        the result count, not table size. Rows without a ticket are dropped."""
        candidates = {self._ticket_of(row) for row in results}
        candidates.discard(None)
        if not candidates:
            return []
        allowed = set(
            frappe.get_list(
                "HD Ticket", filters={"name": ["in", list(candidates)]}, pluck="name"
            )
        )
        return [r for r in results if self._ticket_of(r) in allowed]

    @staticmethod
    def _ticket_of(result: dict) -> str | None:
        """Communication rows carry their ticket in reference_name, not reference_ticket."""
        return result.get("reference_ticket") or result.get("reference_name")

    def _get_accessible_tickets(self):
        """Get tickets accessible to current user based on helpdesk permissions."""
        return frappe.get_list("HD Ticket", pluck="name")

    def prepare_document(self, doc):
        """Prepare a document for indexing with helpdesk-specific handling."""
        document = super().prepare_document(doc)
        if not document:
            return None

        if (
            doc.doctype == "HD Ticket Comment"
            and doc.reference_ticket
            and type(doc.reference_ticket) is str
        ):
            document["reference_ticket"] = str(doc.reference_ticket)

        if doc.doctype == "Communication":
            # For communications, ensure reference fields are set for ticket doctype
            document["reference_doctype"] = doc.reference_doctype
            if (
                doc.reference_doctype == "HD Ticket"
                and doc.reference_name
                and type(doc.reference_name) is str
            ):
                document["reference_name"] = str(doc.reference_name)

        if doc.doctype == "HD Ticket":
            document["reference_ticket"] = str(doc.name)

        # Map commented_by to owner for HD Ticket Comment
        if doc.doctype == "HD Ticket Comment":
            document["owner"] = doc.commented_by

        # Map sender to owner for Communication
        if doc.doctype == "Communication":
            document["owner"] = doc.sender

        return document

    def get_filter_options(self):
        """Get available filter options for search interface."""
        if not self.index_exists():
            return {
                "teams": {},
                "statuses": {},
                "priorities": {},
                "customers": {},
                "doctypes": {},
            }

        # Get accessible tickets first
        accessible_tickets = self._get_accessible_tickets()
        if not accessible_tickets:
            return {
                "teams": {},
                "statuses": {},
                "priorities": {},
                "customers": {},
                "doctypes": {},
            }

        # The ticket list binds as one json variable per column instead of 3N
        # placeholders, which hit SQLite's bound-variable ceiling. Three columns
        # because each row type stores its ticket in a different one.
        sql = """
			SELECT
				agent_group,
				status,
				priority,
				customer,
				doctype,
				COUNT(*) as count
			FROM search_fts
			WHERE (name IN (SELECT value FROM json_each(?))
				OR reference_name IN (SELECT value FROM json_each(?))
				OR reference_ticket IN (SELECT value FROM json_each(?)))
			GROUP BY agent_group, status, priority, customer, doctype
		"""

        tickets_json = frappe.as_json(accessible_tickets)
        results = self.sql(sql, [tickets_json] * 3, read_only=True)

        # Aggregate the results
        teams = {}
        statuses = {}
        priorities = {}
        customers = {}
        doctypes = {}

        for row in results:
            if row["agent_group"]:
                teams[row["agent_group"]] = (
                    teams.get(row["agent_group"], 0) + row["count"]
                )
            if row["status"]:
                statuses[row["status"]] = statuses.get(row["status"], 0) + row["count"]
            if row["priority"]:
                priorities[row["priority"]] = (
                    priorities.get(row["priority"], 0) + row["count"]
                )
            if row["customer"]:
                customers[row["customer"]] = (
                    customers.get(row["customer"], 0) + row["count"]
                )
            if row["doctype"]:
                doctypes[row["doctype"]] = (
                    doctypes.get(row["doctype"], 0) + row["count"]
                )

        return {
            "teams": teams,
            "statuses": statuses,
            "priorities": priorities,
            "customers": customers,
            "doctypes": doctypes,
        }


def build_index():
    """Build search index - can be called from console."""
    search = HelpdeskSearch()
    search.build_index()
