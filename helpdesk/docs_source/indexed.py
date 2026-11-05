from urllib.parse import urlsplit

import frappe
from frappe import _
from frappe.utils import md_to_html

from helpdesk.docs_source import DocsSource
from helpdesk.docs_source.fetch import DocsFetchError, fetch_live
from helpdesk.docs_source.index import PAGES_KEY, DocsIndex
from helpdesk.docs_source.text import clean_html, clean_markdown, has_dot_segment, rewrite_links

PAGE_SECONDS = 600
CACHE = "helpdesk_docs_llms"
GONE_STATUSES = (404, 410)


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
        return {
            "title": page["title"],
            "content": rewrite_links(self._read_html(page), page["url"], self._is_page),
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

    def _read_html(self, page: dict) -> str:
        key = f"{CACHE}:{page['url']}"
        if (html := frappe.cache.get_value(key)) is None:
            try:
                text = fetch_live(page["url"], self.host).text
            except DocsFetchError as e:
                if e.status in GONE_STATUSES:
                    raise frappe.DoesNotExistError(_("Docs page not found")) from None
                raise
            html = clean_html(md_to_html(clean_markdown(text, page["title"])))
            frappe.cache.set_value(key, html, expires_in_sec=PAGE_SECONDS)
        return html

    def _is_page(self, route: str) -> bool:
        return not has_dot_segment(route) and frappe.cache.hexists(PAGES_KEY, route)
