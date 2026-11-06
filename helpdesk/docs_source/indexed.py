import re
from urllib.parse import urlsplit

import frappe
from frappe import _
from frappe.utils import md_to_html
from redis.exceptions import RedisError

from helpdesk.docs_source import DocsSource
from helpdesk.docs_source.fetch import DocsFetchError, fetch, fetch_live
from helpdesk.docs_source.index import PAGES_KEY, DocsIndex
from helpdesk.docs_source.text import (
    clean_html,
    clean_markdown,
    has_dot_segment,
    rewrite_links,
    text_title,
)

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
        self.base_path = urlsplit(self.url).path

    def read_pages(self) -> tuple[str, list[dict]]:
        """The label and pages, each `{"route", "title", "url", "body"}`."""
        raise NotImplementedError

    def search(self, query: str) -> list[dict]:
        return DocsIndex().find(query)

    def get_page(self, route: str, live: bool = True) -> dict:
        route = route.strip("/")
        if has_dot_segment(route):
            raise frappe.DoesNotExistError(_("Docs page not found"))
        page = frappe.cache.hget(PAGES_KEY, route) or self._unindexed_page(route)
        if not page:
            raise frappe.DoesNotExistError(_("Docs page not found"))
        read = self._read(page, live)
        return {
            "route": route,
            "title": page["title"] or read["title"] or route.rpartition("/")[2],
            "content": rewrite_links(read["html"], page["url"], self._is_page),
            "label": page["label"],
            "last_updated": None,
            "source_url": page["url"].removesuffix(".md"),
            "site_url": self.url,
        }

    def list_pages(self, section: str | None = None) -> list[dict]:
        pages = []
        for route, page in (frappe.cache.hgetall(PAGES_KEY) or {}).items():
            route = route if isinstance(route, str) else route.decode()
            key = self.section_of(route)
            if section in (None, key):
                pages.append({"route": route, "title": page["title"], "section": key})
        return pages

    def sections(self) -> list[dict]:
        return []

    def section_of(self, route: str) -> str:
        """The first path segment below the connected path."""
        base = f"{self.base_path.strip('/')}/"
        return route.removeprefix(base).partition("/")[0]

    def _unindexed_page(self, route: str) -> dict | None:
        """A page to read live with no index, as after a build flushes Redis."""
        if not self._can_read_unindexed(route):
            return None
        try:
            if DocsIndex().index_exists():
                return None
        except RedisError:
            return None
        return {
            "title": "",
            "url": self._page_url(route),
            "label": self.host,
            "unindexed": True,
        }

    def _can_read_unindexed(self, route: str) -> bool:
        # The route is reader input, with no index entry to vouch for it.
        return (
            bool(route)
            and not set(route) & set("?#\\")
            and self._is_in_scope(f"/{route}")
        )

    def _is_in_scope(self, path: str) -> bool:
        return path == self.base_path or path.startswith(f"{self.base_path}/")

    def _page_url(self, route: str) -> str:
        return f"https://{self.host}/{route}.md"

    def _read(self, page: dict, live: bool = True) -> dict:
        """The page's cached `{"title", "html"}`, with the title found in its body."""
        key = f"{CACHE}:{page['url']}"
        if (read := frappe.cache.get_value(key)) is None:
            try:
                response = (fetch_live if live else fetch)(page["url"], self.host)
            except DocsFetchError as e:
                if e.status in GONE_STATUSES:
                    raise frappe.DoesNotExistError(_("Docs page not found")) from None
                raise
            # No index entry vouches for this page, so a redirect must stay in scope.
            final_path = urlsplit(response.url).path
            if page.get("unindexed") and not self._is_in_scope(final_path):
                raise frappe.DoesNotExistError(_("Docs page not found"))
            text = response.text
            title = page["title"] or self._title_of(text)
            read = {"title": title, "html": self._to_html(text, title)}
            frappe.cache.set_value(key, read, expires_in_sec=PAGE_SECONDS)
        return read

    def _title_of(self, text: str) -> str:
        """The title in a fetched page body; Markdown by default."""
        heading = re.search(r"^# (.+)$", text, re.M)
        return text_title(heading[1]) if heading else ""

    def _to_html(self, text: str, title: str) -> str:
        """Safe HTML for a fetched page body; Markdown by default."""
        return clean_html(md_to_html(clean_markdown(text, title)))

    def _is_page(self, route: str) -> bool:
        return not has_dot_segment(route) and frappe.cache.hexists(PAGES_KEY, route)
