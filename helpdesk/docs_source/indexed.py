from urllib.parse import urlsplit

import frappe
from frappe import _
from frappe.utils import md_to_html

from helpdesk.docs_source import DocsSource
from helpdesk.docs_source.fetch import fetch_live
from helpdesk.docs_source.index import PAGES_KEY, DocsIndex
from helpdesk.docs_source.text import clean_html, clean_markdown, has_dot_segment, rewrite_links

PAGE_SECONDS = 600
CACHE = "helpdesk_docs_llms"


class IndexedSource(DocsSource):
    """A source searched through the local index; pages are read live from the site."""

    # Set by read_pages when it had to stop early.
    truncated = False

    def __init__(self, url: str) -> None:
        self.url = url.rstrip("/")
        self.host = urlsplit(self.url).hostname

    def read_pages(self) -> tuple[str, list[dict]]:
        """The label and pages, each `{"route", "title", "url", "body"}`."""
        raise NotImplementedError

    def search(self, query: str) -> list[dict]:
        return DocsIndex().find(query)

    def get_page(self, route: str) -> dict:
        route = route.strip("/")
        page = None if has_dot_segment(route) else frappe.cache.hget(PAGES_KEY, route)
        if not page:
            raise frappe.DoesNotExistError(_("Docs page not found"))
        html = md_to_html(clean_markdown(self._read_markdown(page["url"]), page["title"]))
        return {
            "title": page["title"],
            "content": rewrite_links(clean_html(html), page["url"], self._is_page),
            "label": page["label"],
            "last_updated": None,
            "source_url": page["url"].removesuffix(".md"),
            "site_url": self.url,
        }

    def list_pages(self, section: str | None = None) -> list[dict]:
        pages = []
        for route, page in (frappe.cache.hgetall(PAGES_KEY) or {}).items():
            route = route if isinstance(route, str) else route.decode()
            key = route.partition("/")[0]
            if section in (None, key):
                pages.append({"route": route, "title": page["title"], "section": key})
        return pages

    def sections(self) -> list[dict]:
        return []

    def _read_markdown(self, url: str) -> str:
        key = f"{CACHE}:{url}"
        if (text := frappe.cache.get_value(key)) is None:
            text = fetch_live(url, self.host).text
            frappe.cache.set_value(key, text, expires_in_sec=PAGE_SECONDS)
        return text

    def _is_page(self, route: str) -> bool:
        return not has_dot_segment(route) and frappe.cache.hexists(PAGES_KEY, route)
