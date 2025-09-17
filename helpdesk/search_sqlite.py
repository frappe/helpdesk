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
            "reference_ticket"
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
                "owner"
            ],
        },
        "HD Ticket Comment": {
            "fields": [
                "name",
                "content",
                "modified",
                "reference_ticket",
                "commented_by",
                "owner"
            ],
        },
        "Communication": {
            "fields": [
                "name",
                {"title": "subject"},
                "content",
                "modified",
                "reference_doctype",
                "reference_name",
                "sender",
                "owner"
            ],
            "filters": {"reference_doctype": "HD Ticket"},
        },
    }

    def get_search_filters(self):
        """Return permission filters based on accessible tickets."""

        if "System Manager" in frappe.get_roles():
            return {}

        accessible_tickets = self._get_accessible_tickets()

        if not accessible_tickets:
            return {"name": []}  # No accessible tickets

        return {
            "reference_ticket": accessible_tickets,
            "reference_name": accessible_tickets,
            "name": accessible_tickets
        }

    def _get_accessible_tickets(self):
        """Get tickets accessible to current user based on helpdesk permissions."""
        from helpdesk.utils import is_agent

        user = frappe.session.user

        if user == "Administrator":
            return frappe.get_all("HD Ticket", pluck="name")

        if is_agent(user):
            # Agent can see tickets in their teams + assigned tickets
            agent_teams = frappe.get_all("HD Team Member",
                filters={"user": user}, pluck="parent")

            assigned_tickets = []
            if frappe.db.exists("HD Ticket", {"_assign": ("like", f"%{user}%")}):
                assigned_tickets = frappe.get_all("HD Ticket",
                    filters={"_assign": ("like", f"%{user}%")}, pluck="name")

            team_tickets = []
            if agent_teams:
                team_tickets = frappe.get_all("HD Ticket",
                    filters={"agent_group": ("in", agent_teams)}, pluck="name")

            return list(set(assigned_tickets + team_tickets))

        # Non-agents have no search access
        return []

    def prepare_document(self, doc):
        """Prepare a document for indexing with helpdesk-specific handling."""
        document = super().prepare_document(doc)
        if not document:
            return None

        if doc.doctype == "HD Ticket Comment":
            # For comments, resolve the ticket for permissions
            document["reference_ticket"] = doc.reference_ticket

        if doc.doctype == "Communication":
            # For communications, ensure reference fields are set
            document["reference_doctype"] = doc.reference_doctype
            document["reference_name"] = doc.reference_name

        # Map raised_by to customer for HD Ticket
        if doc.doctype == "HD Ticket":
            document["customer"] = doc.raised_by

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
                "doctypes": {}
            }

        # Get accessible tickets first
        accessible_tickets = self._get_accessible_tickets()
        if not accessible_tickets:
            return {
                "teams": {},
                "statuses": {},
                "priorities": {},
                "customers": {},
                "doctypes": {}
            }

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
            WHERE (name IN ({placeholders}) OR reference_name IN ({placeholders}) OR reference_ticket IN ({placeholders}))
            GROUP BY agent_group, status, priority, customer, doctype
        """.format(placeholders=",".join(["?" for _ in accessible_tickets]))

        params = accessible_tickets * 3
        results = self.sql(sql, params, read_only=True)

        # Aggregate the results
        teams = {}
        statuses = {}
        priorities = {}
        customers = {}
        doctypes = {}

        for row in results:
            if row["agent_group"]:
                teams[row["agent_group"]] = teams.get(row["agent_group"], 0) + row["count"]
            if row["status"]:
                statuses[row["status"]] = statuses.get(row["status"], 0) + row["count"]
            if row["priority"]:
                priorities[row["priority"]] = priorities.get(row["priority"], 0) + row["count"]
            if row["customer"]:
                customers[row["customer"]] = customers.get(row["customer"], 0) + row["count"]
            if row["doctype"]:
                doctypes[row["doctype"]] = doctypes.get(row["doctype"], 0) + row["count"]

        return {
            "teams": teams,
            "statuses": statuses,
            "priorities": priorities,
            "customers": customers,
            "doctypes": doctypes,
        }


def build_index():
    """Build search index - called by background job."""
    search = HelpdeskSearch()
    search.build_index()


def build_index_in_background():
    """Build index in background if not already in progress."""
    if not frappe.cache().get_value("helpdesk_sqlite_search_indexing_in_progress"):
        frappe.enqueue(build_index, queue="long")


def build_index_if_not_exists():
    """Build index if it doesn't exist."""
    search = HelpdeskSearch()
    if not search.index_exists():
        build_index_in_background()


def update_doc_index(doc, method=None):
    """Update search index when document is created/updated."""
    search = HelpdeskSearch()
    if search.is_search_enabled() and search.index_exists():
        document = search.prepare_document(doc)
        if document:
            search._index_documents([document])


def delete_doc_index(doc, method=None):
    """Remove document from search index when deleted."""
    search = HelpdeskSearch()
    if search.is_search_enabled() and search.index_exists():
        doc_id = f"{doc.doctype}:{doc.name}"
        try:
            conn = search._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM search_fts WHERE doc_id = ?", (doc_id,))
            conn.commit()
            conn.close()
        except Exception as e:
            frappe.log_error(f"Failed to delete document from search index: {e}")


# Migration utilities
@frappe.whitelist()
def migrate_to_sqlite_search():
    """Admin-only migration from Redis to SQLite search"""
    if not frappe.has_permission("HD Settings", "write"):
        frappe.throw("Insufficient permissions")

    # Build SQLite index
    frappe.enqueue(build_index, queue="long")

    return {"message": "SQLite search index build started"}


@frappe.whitelist()
def get_search_status():
    """Get status of both search systems"""
    search = HelpdeskSearch()

    # Check SQLite search status
    sqlite_status = {
        "enabled": search.is_search_enabled(),
        "exists": search.index_exists(),
        "documents": 0
    }

    if sqlite_status["exists"]:
        try:
            result = search.sql("SELECT COUNT(*) as count FROM search_fts", read_only=True)
            sqlite_status["documents"] = result[0]["count"] if result else 0
        except Exception:
            sqlite_status["documents"] = 0

    # Check Redis search status
    redis_status = {"exists": False, "documents": 0}
    try:
        from helpdesk.search import HelpdeskSearch as RedisSearch
        redis_search = RedisSearch()
        redis_status["exists"] = redis_search.index_exists()
        if redis_status["exists"]:
            redis_status["documents"] = redis_search.num_records()
    except Exception:
        pass

    return {
        "sqlite": sqlite_status,
        "redis": redis_status
    }


@frappe.whitelist()
def rebuild_sqlite_index():
    """Rebuild SQLite search index - admin only"""
    if not frappe.has_permission("HD Settings", "write"):
        frappe.throw("Insufficient permissions")

    frappe.enqueue(build_index, queue="long")
    return {"message": "SQLite search index rebuild started"}
