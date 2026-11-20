"""Ticket search backend selection and document lifecycle."""

import os
from typing import Protocol

import frappe
from frappe import _
from frappe.search.sqlite_search import (
    SQLiteSearchIndexMissingError as SearchIndexMissingError,
)
from frappe.utils.synchronization import filelock
from rq import Retry

from helpdesk.search_sqlite import HelpdeskSearch


class SearchBackend(Protocol):
    def search(self, query, title_only=False, filters=None):
        """Return permission-filtered results and summary."""

    def get_filter_options(self):
        """Count visible documents by filter value."""

    def index_exists(self):
        """Whether a completed index is available."""

    def needs_build(self):
        """Whether an initial or interrupted build needs processing."""

    def build_index(self, force=False, refresh=False):
        """Build or resume; refresh only in a background-owned transaction."""

    def index_doc(self, doctype, name, refresh=False):
        """Synchronize a document with its current database state."""

    def remove_doc(self, doctype, name):
        """Remove a deleted document from the index."""


class SQLiteBackend:
    def __init__(self):
        self.search_index = HelpdeskSearch()

    def search(self, query, title_only=False, filters=None):
        return self.search_index.search(query, title_only=title_only, filters=filters)

    def get_filter_options(self):
        return self.search_index.get_filter_options()

    def index_exists(self):
        return self.search_index.index_exists()

    def needs_build(self):
        return not self.index_exists() or os.path.exists(
            self.search_index._get_db_path(is_temp=True)
        )

    def build_index(self, force=False, refresh=False):
        with filelock(
            "search_index_helpdesk.search_sqlite.HelpdeskSearch", timeout=7800
        ):
            if refresh:
                frappe.db.rollback()
            if force:
                self.search_index.drop_index()
            continuation = os.path.exists(self.search_index._get_db_path(is_temp=True))
            if continuation or not self.index_exists():
                self.search_index.build_index(
                    is_continuation=continuation and not force
                )
        if self.index_exists():
            self.drain_queue(refresh=refresh)

    def index_doc(self, doctype, name, refresh=False):
        with filelock(
            "search_index_helpdesk.search_sqlite.HelpdeskSearch", timeout=7800
        ):
            if refresh:
                frappe.db.rollback()
            if not self.index_exists():
                raise SearchIndexMissingError("Ticket search index is not available")
            self.search_index.remove_doc(doctype, name)
            if is_indexable(doctype, name):
                self.search_index.index_documents_by_name(doctype, [name])

    def remove_doc(self, doctype, name):
        if self.index_exists():
            with filelock(
                "search_index_helpdesk.search_sqlite.HelpdeskSearch", timeout=7800
            ):
                self.search_index.remove_doc(doctype, name)

    def drain_queue(self, refresh=False):
        # Preserve updates queued by the previous framework-owned lifecycle.
        rows = self.search_index.sql(
            "SELECT doc_id FROM search_index_queue", read_only=True
        )
        for row in rows:
            doctype, name = row["doc_id"].split(":", 1)
            if doctype in HelpdeskSearch.INDEXABLE_DOCTYPES:
                self.index_doc(doctype, name, refresh=refresh)


def get_search_backend() -> SearchBackend:
    backend = frappe.conf.get("helpdesk_search_backend", "sqlite")
    if backend == "sqlite":
        return SQLiteBackend()
    if backend == "redis":
        from helpdesk.search_redis import RedisSearchBackend

        return RedisSearchBackend()
    frappe.throw(_("Unknown Helpdesk search backend: {0}").format(backend))


def is_indexable(doctype, name):
    config = HelpdeskSearch.INDEXABLE_DOCTYPES.get(doctype)
    if not config:
        return False
    return bool(frappe.db.exists(doctype, {"name": name, **config.get("filters", {})}))


def build_index(force=False, refresh=False):
    """Build the selected backend's index from the site's documents."""
    get_search_backend().build_index(force=force, refresh=refresh)


def build_index_in_background():
    frappe.enqueue(
        "helpdesk.ticket_search.build_index",
        queue="long",
        job_id="helpdesk_ticket_search_build",
        deduplicate=True,
        enqueue_after_commit=True,
        timeout=7800,
        refresh=True,
        rq_retry=Retry(max=3),
    )


def build_index_if_not_exists():
    if get_search_backend().needs_build():
        build_index_in_background()


def update_doc_index(doc, method=None):
    if doc.doctype in HelpdeskSearch.INDEXABLE_DOCTYPES:
        frappe.enqueue(
            "helpdesk.ticket_search.sync_document",
            queue="long",
            enqueue_after_commit=True,
            doctype=doc.doctype,
            name=doc.name,
            timeout=8100,
            rq_retry=Retry(max=3),
        )


def rename_doc_index(doc, method=None, old=None, new=None, merge=False):
    if doc.doctype not in HelpdeskSearch.INDEXABLE_DOCTYPES:
        return
    if old:
        frappe.enqueue(
            "helpdesk.ticket_search.sync_document",
            queue="long",
            enqueue_after_commit=True,
            doctype=doc.doctype,
            name=old,
            timeout=8100,
            rq_retry=Retry(max=3),
        )
    update_doc_index(doc)


def sync_document(doctype, name):
    """Read committed state, so delayed jobs cannot restore deleted documents."""
    if doctype not in HelpdeskSearch.INDEXABLE_DOCTYPES:
        return
    get_search_backend().index_doc(doctype, name, refresh=True)
