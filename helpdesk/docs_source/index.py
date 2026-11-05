import frappe
from redis.exceptions import ResponseError

from helpdesk.api.article import _as_mark
from helpdesk.api.knowledge_base import escape_marked
from helpdesk.search import Search, get_stopwords

INDEX = "helpdesk_docs_idx"
PREFIX = "docs_page"
PAGES_KEY = "helpdesk_docs_pages"
PAGE_LENGTH = 20


class DocsIndex(Search):
    """RediSearch index of Docs pages from a source without a live search API."""

    def __init__(self) -> None:
        schema = [
            {"name": "subject", "weight": 6},
            {"name": "description", "weight": 5},
            {"name": "route", "no_index": True, "sortable": True},
            {"name": "label", "no_index": True, "sortable": True},
        ]
        super().__init__(INDEX, PREFIX, schema)

    def replace(self, pages: list[dict], label: str) -> None:
        """Swap in `pages`. Raises ResponseError when redis has no RediSearch."""
        self.clear()
        self.create_index()
        for page in pages:
            self.add_document(
                page["route"],
                {
                    "subject": page["title"],
                    "description": page["body"],
                    "route": page["route"],
                    "label": label,
                },
            )
            frappe.cache.hset(
                PAGES_KEY,
                page["route"],
                {"title": page["title"], "url": page["url"], "label": label},
            )

    def clear(self) -> None:
        self.drop_index()
        frappe.cache.delete_value(PAGES_KEY)
        self._index_exists = False

    def find(self, query: str) -> list[dict]:
        words = [w for w in self.clean_query(query).split() if w not in get_stopwords()]
        if not words:
            return []
        terms = " ".join([*words[:-1], f"{words[-1]}*"])
        # Title matches first: DISMAX alone ranks them below long pages.
        hits: dict[str, dict] = {}
        try:
            for search in (f"@subject:({terms})", terms):
                for doc in self.search(search, page_length=PAGE_LENGTH, highlight=True).docs:
                    hits.setdefault(doc.route, self._to_hit(doc))
        except ResponseError:
            return []
        return list(hits.values())

    def index_exists(self) -> bool:
        if not hasattr(self, "_index_exists"):
            try:
                self.redis.ft(self.index_name).info()
                self._index_exists = True
            except ResponseError:
                self._index_exists = False
        return self._index_exists

    def _to_hit(self, doc) -> dict:
        return {
            "route": doc.route,
            "title": escape_marked(_as_mark(doc.subject)),
            "excerpt": escape_marked(_as_mark(doc.description)),
            "category_label": doc.label,
        }
