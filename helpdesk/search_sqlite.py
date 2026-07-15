# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

import frappe
from frappe.search.sqlite_search import SQLiteSearch, SQLiteSearchIndexMissingError


class HelpdeskSearchIndexMissingError(SQLiteSearchIndexMissingError):
    pass


class HelpdeskSearch(SQLiteSearch):
    INDEX_NAME = "helpdesk_search.db"

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

    def get_search_filters(self):
        """Return permission filters based on accessible tickets."""
        if self._has_unrestricted_ticket_access():
            # No ticket-level restriction applies (see permission_query): every
            # ticket is visible, so skip building a reference_ticket IN (...)
            # list. For such users that list is the entire ticket table, which
            # can exceed SQLite's variable limit and make search() fail (it
            # swallows the OperationalError and silently returns no results).
            return {}
        return {"reference_ticket": self._get_accessible_tickets()}

    def _has_unrestricted_ticket_access(self):
        """Whether the current user can see every ticket.

        ``permission_query`` returns ``None`` (no WHERE fragment) for admins,
        and for agents when ``restrict_tickets_by_agent_group`` is disabled --
        i.e. when there is no ticket-level restriction to express.
        """
        from helpdesk.helpdesk.doctype.hd_ticket.hd_ticket import permission_query

        return permission_query(frappe.session.user) is None

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

        # Restrict facet counts to accessible tickets. Users with unrestricted
        # access can see every ticket, so count the whole index instead of
        # binding the entire ticket table into an IN (...) clause (which grows
        # to 3N host parameters here and can exceed SQLite's variable limit).
        if self._has_unrestricted_ticket_access():
            where_clause = ""
            params = []
        else:
            accessible_tickets = self._get_accessible_tickets()
            if not accessible_tickets:
                return {
                    "teams": {},
                    "statuses": {},
                    "priorities": {},
                    "customers": {},
                    "doctypes": {},
                }
            placeholders = ",".join(["?" for _ in accessible_tickets])
            where_clause = (
                "WHERE (name IN ({p}) OR reference_name IN ({p}) "
                "OR reference_ticket IN ({p}))".format(p=placeholders)
            )
            params = accessible_tickets * 3

        # Query the search index for available options
        sql = """
			SELECT
				agent_group,
				status,
				priority,
				customer,
				doctype,
				COUNT(*) as count
			FROM search_fts
			{where_clause}
			GROUP BY agent_group, status, priority, customer, doctype
		""".format(
            where_clause=where_clause
        )

        results = self.sql(sql, params, read_only=True)

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
