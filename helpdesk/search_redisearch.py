# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

"""RediSearch backend for Helpdesk ticket search.

A drop-in alternative to :class:`helpdesk.search_sqlite.HelpdeskSearch` for
deployments where the SQLite FTS index cannot run — notably high-availability
topologies with ``sites/`` on a network filesystem, where SQLite's WAL mode
requires shared memory between all processes on one host and therefore breaks
(https://www.sqlite.org/wal.html).

It exposes the same public surface (``search``, ``get_filter_options``,
``index_exists``, ``build_index``, ``index_doc``, ``remove_doc``) returning the
same shapes, so ``helpdesk.api.search`` and the frontend are unaffected — only
the storage engine changes, selected by ``HD Settings.search_backend``.

Design notes:
- Documents are stored as Redis hashes under a shared prefix and queried through
  a RediSearch index (``frappe.cache().ft(...)``), the same pattern webshop and
  wiki use. It requires the RediSearch module loaded in the cache Redis.
- The redis-search client APIs are imported lazily inside the methods that use
  them (as ``wiki`` does), so importing this module on a SQLite-only site — which
  happens because ``hooks.py`` wires migration/scheduler/doc events here — never
  requires ``redis.commands.search`` to be present.
- Permission is never materialised as a giant list of ticket names (the volume
  problem that makes the SQLite ``get_filter_options`` fail at scale). Instead:
  * ``search`` post-filters query matches through the real ticket permission
    (``frappe.get_list``), paginating until the caller's ``limit`` is filled or
    the matches are exhausted (so a readable ticket is never skipped), and never
    exposes pre-permission match counts;
  * ``get_filter_options`` aggregates straight from the database honouring the
    real ``permission_query``, decoupled from the search index entirely.
"""

import contextlib
import re
import time

import frappe
from frappe.utils import get_datetime, strip_html_tags
from frappe.utils.redis_wrapper import RedisWrapper

from helpdesk.search_sqlite import HelpdeskSearchIndexMissingError

INDEX_NAME = "helpdesk_ticket_idx"
KEY_PREFIX = "hd_ticket_search:"

# Which doctypes are indexed and how each maps onto the shared document shape.
# Mirrors HelpdeskSearch.INDEXABLE_DOCTYPES + prepare_document, kept local so the
# backend is self-contained (depends only on frappe + redis).
INDEXED_DOCTYPES = ("HD Ticket", "HD Ticket Comment", "Communication")

# Fields carried on every indexed document (hash keys / index schema).
TEXT_FIELDS = ("title", "content")
TAG_FIELDS = (
    "doctype",
    "name",
    "reference_ticket",
    "reference_name",
    "reference_doctype",
    "agent_group",
    "status",
    "priority",
    "customer",
    "owner",
)

_UNSAFE_QUERY_CHARS = re.compile(r"[^a-zA-Z0-9\s]")
_MIN_PREFIX_LEN = 3

# Result window. The API accepts ``limit`` (default 20, hard cap 100); the
# backend honours it. To fill ``limit`` permitted rows without ever enumerating
# the full accessible set, it scans query matches in pages, post-filtering each
# through the real permission, until the limit is filled or the matches are
# exhausted — so a readable ticket is never skipped, whatever its rank.
DEFAULT_LIMIT = 20
MAX_LIMIT = 100
CANDIDATE_PAGE = 100

# RediSearch splits a TAG value on this character. It must be one that cannot
# occur in the indexed values (ticket ids, statuses, team/customer names,
# emails) so each value is stored as a single exact tag — otherwise a customer
# like "Acme, Inc" would be split on the default comma and never match its
# escaped filter.
TAG_SEPARATOR = "\n"


def _response_error():
    from redis import ResponseError

    return ResponseError


def _index_definition_cls():
    try:
        from redis.commands.search.index_definition import IndexDefinition
    except ImportError:  # older redis-py
        from redis.commands.search.indexDefinition import IndexDefinition
    return IndexDefinition


def is_search_module_loaded() -> bool:
    """True only if the RediSearch module is loaded in the cache Redis."""
    try:
        for module in frappe.cache().module_list():
            if module.get(b"name") == b"search":
                return True
    except Exception:
        return False
    return False


class HelpdeskRediSearch:
    """RediSearch-backed ticket search with the HelpdeskSearch public surface."""

    def __init__(self):
        self.cache = frappe.cache()
        self.index_name = self.cache.make_key(INDEX_NAME).decode()

    # ------------------------------------------------------------------ index

    def _index(self):
        return self.cache.ft(INDEX_NAME)

    def index_exists(self) -> bool:
        try:
            self._index().info()
            return True
        except Exception:
            return False

    def raise_if_not_indexed(self):
        if not self.index_exists():
            raise HelpdeskSearchIndexMissingError(
                "Search index does not exist. Please build the index first."
            )

    def drop_index(self, delete_documents: bool = True):
        # Suppress the "unknown index" error when there is nothing to drop.
        with contextlib.suppress(_response_error()):
            self._index().dropindex(delete_documents=delete_documents)

    def create_index(self):
        from redis.commands.search.field import NumericField, TagField, TextField

        schema = (
            [TextField(f) for f in TEXT_FIELDS]
            + [TagField(f, separator=TAG_SEPARATOR) for f in TAG_FIELDS]
            + [NumericField("modified", sortable=True)]
        )
        definition = _index_definition_cls()(
            prefix=[self.cache.make_key(KEY_PREFIX).decode()]
        )
        self._index().create_index(schema, definition=definition)

    def build_index(self):
        """Rebuild the whole index from scratch (drop + create + reindex)."""
        if not is_search_module_loaded():
            frappe.log_error(
                title="Helpdesk RediSearch",
                message="RediSearch module not loaded in cache Redis; index not built.",
            )
            return
        self.drop_index()
        self.create_index()
        for doctype in INDEXED_DOCTYPES:
            for name in self._doctype_docnames(doctype):
                self.index_doc(doctype, name, ensure=False)

    # --------------------------------------------------------------- document

    def _doc_key(self, doctype: str, name: str) -> str:
        return self.cache.make_key(f"{KEY_PREFIX}{doctype}:{name}").decode()

    def _doctype_docnames(self, doctype: str) -> list[str]:
        filters = {}
        if doctype == "Communication":
            filters = {"reference_doctype": "HD Ticket"}
        return frappe.get_all(doctype, filters=filters, pluck="name")

    def prepare_document(self, doc) -> dict | None:
        """Build the flat hash for one document. Returns None if not indexable."""
        base = dict.fromkeys((*TEXT_FIELDS, *TAG_FIELDS), "")
        base["doctype"] = doc.doctype
        base["name"] = str(doc.name)

        if doc.doctype == "HD Ticket":
            base["title"] = strip_html_tags(doc.get("subject") or "")
            base["content"] = strip_html_tags(doc.get("description") or "")
            base["agent_group"] = doc.get("agent_group") or ""
            base["status"] = doc.get("status") or ""
            base["priority"] = doc.get("priority") or ""
            base["customer"] = doc.get("customer") or ""
            base["owner"] = doc.get("owner") or ""
            base["reference_ticket"] = str(doc.name)
        elif doc.doctype == "HD Ticket Comment":
            base["content"] = strip_html_tags(doc.get("content") or "")
            base["reference_ticket"] = str(doc.get("reference_ticket") or "")
            base["owner"] = doc.get("commented_by") or doc.get("owner") or ""
        elif doc.doctype == "Communication":
            if doc.get("reference_doctype") != "HD Ticket":
                return None
            base["content"] = strip_html_tags(doc.get("content") or "")
            base["reference_doctype"] = "HD Ticket"
            base["reference_name"] = str(doc.get("reference_name") or "")
            base["owner"] = doc.get("sender") or doc.get("owner") or ""
        else:
            return None

        modified = doc.get("modified")
        base["modified"] = get_datetime(modified).timestamp() if modified else 0
        return base

    def index_doc(self, doctype: str, name: str, ensure: bool = True):
        if ensure:
            self.raise_if_not_indexed()
        doc = frappe.get_doc(doctype, name)
        document = self.prepare_document(doc)
        if not document:
            return
        key = self._doc_key(doctype, name)
        # Raw hset (bypass RedisWrapper key-prefixing) — key is already prefixed.
        super(RedisWrapper, self.cache).hset(key, mapping=document)

    def remove_doc(self, doctype: str, name: str):
        # delete_value applies make_key (the site prefix) to match the stored
        # hash key; the plain cache.delete() would target an unprefixed key.
        self.cache.delete_value(f"{KEY_PREFIX}{doctype}:{name}")

    # ----------------------------------------------------------------- search

    def _clean_query(self, query: str) -> str:
        query = _UNSAFE_QUERY_CHARS.sub(" ", query or "").strip().lower()
        return re.sub(r"\s+", " ", query)

    def _build_query_string(self, query: str, title_only: bool, filters: dict) -> str:
        parts = []
        for field, value in (filters or {}).items():
            if field not in TAG_FIELDS or not value:
                continue
            values = value if isinstance(value, list) else [value]
            escaped = "|".join(self._escape_tag(str(v)) for v in values if v)
            if escaped:
                parts.append(f"@{field}:{{{escaped}}}")

        terms = [
            f"{t}*" if len(t) >= _MIN_PREFIX_LEN else t
            for t in self._clean_query(query).split()
        ]
        text = " ".join(terms)
        if text:
            parts.append(f"@title:({text})" if title_only else f"({text})")

        return " ".join(parts) if parts else "*"

    @staticmethod
    def _escape_tag(value: str) -> str:
        """Escape a tag value for a RediSearch ``@field:{...}`` clause.

        Every character RediSearch treats as punctuation inside a tag — including
        the space — is backslash-escaped so multi-word values (a customer or team
        name like ``Acme Corp``) match the tag exactly, the way SQLite would.
        """
        return re.sub(r"([\s,.<>{}\[\]\"'\:;!@#$%^&*()\-+=~|/\\])", r"\\\1", value)

    def search(
        self,
        query: str,
        title_only: bool = False,
        filters: dict | None = None,
        limit: int | None = None,
    ):
        start = time.time()
        self.raise_if_not_indexed()

        filters = filters or {}
        # Empty / punctuation-only query with no filters must not fall through to
        # a "*" match-all — return nothing, mirroring the SQLite backend.
        if not self._clean_query(query) and not filters:
            return self._empty_result(title_only, filters)

        result_cap = min(int(limit or DEFAULT_LIMIT), MAX_LIMIT)
        query_string = self._build_query_string(query, title_only, filters)
        ResponseError = _response_error()
        from redis.commands.search.query import Query

        # Scan query matches in pages, post-filtering each page through the real
        # ticket permission, until the caller's limit is filled or the matches are
        # exhausted. Scanning to exhaustion (bounded by the query's own match
        # count, never the whole corpus) means a readable ticket is never skipped,
        # whatever its rank; a caller still only ever sees the post-permission
        # count, so restricted matches are never inferable.
        permitted: list[dict] = []
        offset = 0
        while len(permitted) < result_cap:
            page = Query(query_string).paging(offset, CANDIDATE_PAGE).with_scores()
            try:
                raw = self._index().search(page)
            except ResponseError as e:
                frappe.log_error(
                    title="Helpdesk RediSearch query failed", message=str(e)
                )
                return self._empty_result(title_only, filters)

            if not raw.docs:
                break
            batch = [
                self._to_result(doc, offset + rank)
                for rank, doc in enumerate(raw.docs, 1)
            ]
            permitted.extend(self._filter_by_permission(batch))
            offset += CANDIDATE_PAGE
            if offset >= raw.total:
                break

        permitted = permitted[:result_cap]
        for i, result in enumerate(permitted, 1):
            result["modified_rank"] = i

        # Only the post-permission count is ever reported, so a caller can never
        # infer that restricted tickets matched the query.
        matched = len(permitted)
        return {
            "results": permitted,
            "summary": {
                "duration": round(time.time() - start, 3),
                "total_matches": matched,
                "returned_matches": matched,
                "corrected_words": None,
                "corrected_query": None,
                "title_only": title_only,
                "filtered_matches": matched,
                "applied_filters": filters,
            },
        }

    def _to_result(self, doc, rank: int) -> dict:
        def get(f):
            return getattr(doc, f, "") or ""

        modified = get("modified")
        result = {
            "id": doc.id,
            "score": float(getattr(doc, "score", 0) or 0),
            "original_rank": rank,
            "bm25_score": float(getattr(doc, "score", 0) or 0),
            "title": get("title"),
            "content": get("content"),
            "doctype": get("doctype"),
            "name": get("name"),
            "reference_ticket": get("reference_ticket"),
            "reference_name": get("reference_name"),
            "reference_doctype": get("reference_doctype"),
            "agent_group": get("agent_group"),
            "status": get("status"),
            "priority": get("priority"),
            "customer": get("customer"),
            "author": get("owner"),
            "modified": float(modified) if modified else None,
        }
        result["_ticket"] = self._result_ticket(result)
        return result

    @staticmethod
    def _result_ticket(result: dict) -> str:
        if result["doctype"] == "HD Ticket":
            return result["name"]
        if result["doctype"] == "HD Ticket Comment":
            return result["reference_ticket"]
        if result["doctype"] == "Communication":
            return result["reference_name"]
        return ""

    def _filter_by_permission(self, results: list[dict]) -> list[dict]:
        """Keep only results whose parent ticket the user may read.

        Bounded to the candidate page, so it reuses the real ticket permission
        (``frappe.get_list`` → helpdesk's ``permission_query``) without ever
        enumerating the full accessible set.
        """
        ticket_names = {r["_ticket"] for r in results if r["_ticket"]}
        if not ticket_names:
            return []
        allowed = set(
            frappe.get_list(
                "HD Ticket", filters={"name": ["in", list(ticket_names)]}, pluck="name"
            )
        )
        cleaned = []
        for r in results:
            if r["_ticket"] in allowed:
                r.pop("_ticket", None)
                cleaned.append(r)
        return cleaned

    def _empty_result(self, title_only, filters):
        return {
            "results": [],
            "summary": {
                "duration": 0,
                "total_matches": 0,
                "returned_matches": 0,
                "corrected_words": None,
                "corrected_query": None,
                "title_only": title_only,
                "filtered_matches": 0,
                "applied_filters": filters or {},
            },
        }

    # ---------------------------------------------------------------- facets

    def get_filter_options(self) -> dict:
        """Available filter facets, computed from the DB under real permission.

        Decoupled from the search index: a single ``frappe.get_list`` over HD
        Ticket applies helpdesk's real permission query (the same call the SQLite
        backend trusts for scoping) as a WHERE clause — no raw SQL and no
        ticket-name ``IN (...)`` enumeration (the volume that made the original
        SQLite ``get_filter_options`` crash at scale). Counts are folded in Python.
        Only ``teams``/``statuses``/``priorities`` are consumed by the frontend;
        ``customers``/``doctypes`` are kept for shape parity with the SQLite
        backend.
        """
        facets = {
            k: {} for k in ("teams", "statuses", "priorities", "customers", "doctypes")
        }

        rows = frappe.get_list(
            "HD Ticket",
            fields=["agent_group", "status", "priority", "customer"],
            limit=0,
        )
        for row in rows:
            self._add(facets["teams"], row.get("agent_group"), 1)
            self._add(facets["statuses"], row.get("status"), 1)
            self._add(facets["priorities"], row.get("priority"), 1)
            self._add(facets["customers"], row.get("customer"), 1)

        if rows:
            facets["doctypes"]["HD Ticket"] = len(rows)

        return facets

    @staticmethod
    def _add(bucket: dict, value, count: int):
        if value:
            bucket[value] = bucket.get(value, 0) + count


def build_index():
    """Build the RediSearch ticket index — callable from console/scheduler."""
    HelpdeskRediSearch().build_index()


# ------------------------------------------------------------------ lifecycle
# doc_event + scheduler handlers, all gated on the toggle so they are inert
# unless the operator has switched ticket search to RediSearch.


def _redisearch_selected() -> bool:
    return frappe.db.get_single_value("HD Settings", "search_backend") == "RediSearch"


def update_ticket_index(doc, method=None):
    if not _redisearch_selected():
        return
    search = HelpdeskRediSearch()
    if not search.index_exists():
        return
    try:
        search.index_doc(doc.doctype, doc.name)
    except Exception:
        frappe.log_error(
            title="Helpdesk RediSearch index update",
            message=f"Failed to index {doc.doctype}:{doc.name}",
        )


def delete_ticket_index(doc, method=None):
    if not _redisearch_selected():
        return
    try:
        HelpdeskRediSearch().remove_doc(doc.doctype, doc.name)
    except Exception:
        frappe.log_error(
            title="Helpdesk RediSearch index delete",
            message=f"Failed to remove {doc.doctype}:{doc.name}",
        )


def build_index_if_enabled():
    """Scheduler entry: build the index if RediSearch is on and it is missing."""
    if not _redisearch_selected():
        return
    search = HelpdeskRediSearch()
    if not search.index_exists():
        search.build_index()


def build_index_in_background():
    """after_migrate entry: (re)build the index in the background if RediSearch is on."""
    if not _redisearch_selected():
        return
    frappe.enqueue("helpdesk.search_redisearch.build_index", queue="long")
