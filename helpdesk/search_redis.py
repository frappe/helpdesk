# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

import html
import re
from time import monotonic

import frappe
from redis.exceptions import ResponseError

from helpdesk.search_sqlite import HelpdeskSearch
from helpdesk.utils import is_agent


class RedisSearchBackend:
    """Shared ticket index; reuse SQLite's document mapping, never its storage."""

    PREFIX = "helpdesk_ticket_search:"
    FILTER_FIELDS = ("agent_group", "status", "priority", "customer", "doctype")
    FACETS = dict(
        zip(FILTER_FIELDS, ("teams", "statuses", "priorities", "customers", "doctypes"))
    )
    PAGE_SIZE = 200

    def __init__(self):
        self.documents = HelpdeskSearch()
        for config in self.documents.doc_configs.values():
            config["fields"] = list(
                dict.fromkeys([*config["fields"], *config["filters"]])
            )
        self.redis = frappe.cache()
        self.namespace = self.redis.make_key(self.PREFIX).decode()
        self.index = self.namespace + "index"
        self.prefix = self.namespace + "doc:"
        self.ready = self.namespace + "ready"

    def _command(self, *args):
        return self.redis.execute_command(*args)

    def _lock(self):
        return self.redis.lock(
            self.namespace + "lock", timeout=600, blocking_timeout=7800
        )

    def _index_created(self):
        try:
            self._command("FT.INFO", self.index)
            return True
        except ResponseError as exc:
            if (
                "unknown index name" in str(exc).lower()
                or "no such index" in str(exc).lower()
            ):
                return False
            raise

    def index_exists(self):
        return self._index_created() and bool(self._command("EXISTS", self.ready))

    def needs_build(self):
        return not self.index_exists()

    def _require_index(self):
        from helpdesk.ticket_search import SearchIndexMissingError

        if not self.index_exists():
            raise SearchIndexMissingError(
                "Ticket search index is not available. Rebuild the index."
            )

    def _drop_index(self):
        self._command("DEL", self.ready)
        if self._index_created():
            self._command("FT.DROPINDEX", self.index, "DD")

    def drop_index(self):
        with self._lock():
            self._drop_index()

    def build_index(self, force=False, refresh=False):
        with self._lock() as lock:
            if refresh:
                frappe.db.rollback()
            if not force and self.index_exists():
                return
            self._drop_index()
            schema = ["title", "TEXT", "WEIGHT", 5, "content", "TEXT"]
            for field in (*self.FILTER_FIELDS, "reference_ticket"):
                schema.extend((field, "TAG", "SEPARATOR", "\x1f", "CASESENSITIVE"))
            self._command(
                "FT.CREATE",
                self.index,
                "ON",
                "HASH",
                "PREFIX",
                1,
                self.prefix,
                "STOPWORDS",
                0,
                "SCHEMA",
                *schema,
            )
            for doctype in self.documents.doc_configs:
                modified = name = None
                while docs := self.documents.get_documents_paginated(
                    doctype,
                    limit=self.PAGE_SIZE,
                    last_indexed_modified=modified,
                    last_indexed_name=name,
                ):
                    for doc in docs:
                        self._write_document(doc)
                    modified, name = docs[-1].creation, docs[-1].name
                    lock.reacquire()
            self._command("SET", self.ready, "1")

    def _key(self, doctype, name):
        return f"{self.prefix}{doctype}:{name}"

    def _write_document(self, doc):
        key = self._key(doc.doctype, doc.name)
        config = self.documents.doc_configs.get(doc.doctype)
        if not config or any(doc.get(k) != v for k, v in config["filters"].items()):
            self._command("DEL", key)
            return
        document = self.documents.prepare_document(doc)
        if not document:
            self._command("DEL", key)
            return
        ticket = str(
            doc.name if doc.doctype == "HD Ticket" else doc.reference_name or ""
        )
        if not ticket or not frappe.db.exists("HD Ticket", ticket):
            self._command("DEL", key)
            return
        document["reference_ticket"] = ticket
        # Raw commands avoid RedisWrapper's cache pickling and key rewriting.
        values = {k: str(v) if v is not None else "" for k, v in document.items()}
        self._command("HSET", key, *(part for pair in values.items() for part in pair))

    def index_doc(self, doctype, docname, refresh=False):
        if doctype not in self.documents.doc_configs:
            return
        with self._lock():
            if refresh:
                frappe.db.rollback()
            self._require_index()
            if not frappe.db.exists(doctype, docname):
                self._remove_doc(doctype, docname)
                return
            self._write_document(frappe.get_doc(doctype, docname))

    def _remove_doc(self, doctype, docname):
        self._command("DEL", self._key(doctype, docname))
        if doctype == "HD Ticket":
            query = "@reference_ticket:{" + self._escape_tag(str(docname)) + "}"
            # Deleting after reading avoids shifting the search pagination.
            keys = [key for key, _ in self._rows(query)]
            for start in range(0, len(keys), self.PAGE_SIZE):
                self._command("DEL", *keys[start : start + self.PAGE_SIZE])

    def remove_doc(self, doctype, docname):
        with self._lock():
            self._require_index()
            # A queued removal may run after the document has been restored.
            if frappe.db.exists(doctype, docname):
                self._write_document(frappe.get_doc(doctype, docname))
            else:
                self._remove_doc(doctype, docname)

    @staticmethod
    def _escape_tag(value):
        return re.sub(r"([^\w])", r"\\\1", value)

    def _query(self, query, title_only, filters):
        if not isinstance(query, str) or len(query) > 512:
            frappe.throw(
                frappe._("Search query must be a string of at most 512 characters")
            )
        words = re.findall(r"\w+", query, flags=re.UNICODE)
        if not words:
            return None
        expression = " ".join(
            self._escape_tag(word) + ("*" if len(word) > 1 else "")
            for word in words[:32]
        )
        if title_only:
            expression = f"@title:({expression})"
        if not isinstance(filters, dict) or set(filters) - set(self.FILTER_FIELDS):
            frappe.throw(frappe._("Invalid search filters"))
        for field, values in filters.items():
            if (
                not isinstance(values, list)
                or len(values) > 50
                or any(
                    not isinstance(value, str) or not value or len(value) > 140
                    for value in values
                )
            ):
                frappe.throw(frappe._("Invalid search filter values"))
            if values:
                expression += (
                    f" @{field}:{{" + "|".join(map(self._escape_tag, values)) + "}"
                )
        return expression

    @staticmethod
    def _text(value):
        return value.decode() if isinstance(value, bytes) else value

    def _rows(self, query):
        fields = list(
            dict.fromkeys(
                [
                    "__key",
                    "id",
                    *self.documents.schema["text_fields"],
                    *self.documents.schema["metadata_fields"],
                ]
            )
        )
        rows, cursor = self._command(
            "FT.AGGREGATE",
            self.index,
            query,
            "ADDSCORES",
            "LOAD",
            len(fields),
            *(f"@{field}" for field in fields),
            "SORTBY",
            4,
            "@__score",
            "DESC",
            "@id",
            "ASC",
            "LIMIT",
            0,
            2147483647,
            "WITHCURSOR",
            "COUNT",
            self.PAGE_SIZE,
            "DIALECT",
            2,
        )
        try:
            while True:
                for values in rows[1:]:
                    row = dict(
                        zip(map(self._text, values[::2]), map(self._text, values[1::2]))
                    )
                    row["score"] = float(row.pop("__score"))
                    yield row.pop("__key"), row
                if not cursor:
                    return
                rows, cursor = self._command(
                    "FT.CURSOR", "READ", self.index, cursor, "COUNT", self.PAGE_SIZE
                )
        finally:
            if cursor:
                self._command("FT.CURSOR", "DEL", self.index, cursor)

    def _permitted_rows(self, query):
        batch = []
        agent = is_agent()
        for _, row in self._rows(query):
            if row.get("doctype") == "Comment" and not agent:
                continue
            batch.append(row)
            if len(batch) == self.PAGE_SIZE:
                yield from self._filter_permissions(batch)
                batch = []
        yield from self._filter_permissions(batch)

    @staticmethod
    def _filter_permissions(rows):
        tickets = {row.get("reference_ticket") for row in rows} - {None, ""}
        if not tickets:
            return []
        allowed = set(
            map(
                str,
                frappe.get_list(
                    "HD Ticket",
                    filters={"name": ["in", list(tickets)]},
                    pluck="name",
                    limit_page_length=0,
                ),
            )
        )
        return [row for row in rows if row.get("reference_ticket") in allowed]

    def search(self, query, title_only=False, filters=None):
        self._require_index()
        started = monotonic()
        filters = filters or {}
        expression = self._query(query, title_only, filters)
        result = self.documents._empty_search_result(title_only, filters)
        count = 0
        if expression:
            for row in self._permitted_rows(expression):
                count += 1
                if len(result["results"]) < 100:
                    row["title"] = html.escape(row.get("title", ""))
                    row["content"] = html.escape(row.get("content", "")[:500])
                    row["preview"] = row["content"]
                    row["author"] = row.get("owner", "")
                    row["modified"] = (
                        float(row["modified"]) if row.get("modified") else None
                    )
                    row["original_rank"] = row["modified_rank"] = count
                    row["bm25_score"] = None
                    result["results"].append(row)
        result["summary"].update(
            total_matches=count,
            filtered_matches=count,
            returned_matches=len(result["results"]),
            duration=round(monotonic() - started, 3),
        )
        return result

    def get_filter_options(self):
        options = {name: {} for name in self.FACETS.values()}
        if not self.index_exists():
            return options
        for row in self._permitted_rows("*"):
            for field, name in self.FACETS.items():
                value = row.get(field)
                if value:
                    options[name][value] = options[name].get(value, 0) + 1
        return options
