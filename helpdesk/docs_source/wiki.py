import re
from urllib.parse import urlsplit

import frappe
from frappe import _
from frappe.utils.html_utils import sanitize_html

from helpdesk.api.knowledge_base import escape_marked
from helpdesk.docs_source import DocsSource
from helpdesk.docs_source.fetch import DocsFetchError, fetch, fetch_live
from helpdesk.docs_source.text import plain_title, rewrite_links

API = "api/method/wiki.frappe_wiki.doctype.wiki_document"
SEARCH_SECONDS = 300
PAGE_SECONDS = 600
SECTIONS_SECONDS = 3600
CACHE = "helpdesk_docs_wiki"
LLMS_LINK = re.compile(r"^\s*- \[(.+?)\]\((\S+?)\)", re.M)
OLD_VERSION = re.compile(r"v\d+")
MOVED_STATUSES = (404, 500)


class WikiSource(DocsSource):
    """Frappe Wiki: live search and pages over its guest APIs."""

    def __init__(self, url: str, hidden: list[str]) -> None:
        self.url = url.rstrip("/")
        self.host = urlsplit(self.url).hostname
        self.hidden = hidden

    def is_available(self) -> bool:
        try:
            return "results" in self._call("search.search", query="docs")
        except (DocsFetchError, KeyError, ValueError):
            return False

    def search(self, query: str) -> list[dict]:
        hits = self._cached(
            f"search:{query.lower()}",
            SEARCH_SECONDS,
            lambda: self._call("search.search", live=True, query=query)["results"],
        )
        return [self._to_hit(hit) for hit in hits if self._is_visible(hit["route"])]

    def get_page(self, route: str) -> dict:
        route = route.strip("/")
        if not self._is_visible(route):
            raise frappe.DoesNotExistError(_("Docs page not found"))
        try:
            return self._get_page(route)
        except DocsFetchError as e:
            if e.status not in MOVED_STATUSES:
                raise
        try:
            return self._get_page(self._follow_redirect(route))
        except DocsFetchError as e:
            if e.status not in MOVED_STATUSES:
                raise
            raise frappe.DoesNotExistError(_("Docs page not found")) from None

    def list_pages(self, section: str | None = None) -> list[dict]:
        keys = [s["key"] for s in self.sections() if section in (None, s["key"])]
        pages = []
        for key in keys:
            if key in self.hidden:
                continue
            for title, link in LLMS_LINK.findall(self._read_llms(f"{key}/llms.txt")):
                route = urlsplit(link).path.strip("/").removesuffix(".md")
                if self._is_visible(route) and self._section_of(route) == key:
                    pages.append({"route": route, "title": plain_title(title), "section": key})
        return pages

    def sections(self) -> list[dict]:
        """Sections of the root llms.txt, without old versions."""
        return [
            {"key": key, "title": title}
            for key, title in self._all_sections().items()
            if not _is_old_version(key)
        ]

    def _get_page(self, route: str) -> dict:
        data = self._cached(
            f"page:{route}",
            PAGE_SECONDS,
            lambda: self._call("wiki_document.get_page_data", live=True, route=route),
        )
        base = f"{self.url}/{route}"
        return {
            "title": data["title"],
            "content": rewrite_links(sanitize_html(data["rendered_content"]), base, self._is_visible),
            "label": f"{self._title_of(route)} docs",
            "last_updated": data.get("last_updated"),
            "source_url": base,
            "site_url": f"{self.url}/{self._section_of(route)}",
        }

    def _follow_redirect(self, route: str) -> str:
        """Final route of a page the API refuses, if it stays on a visible page."""
        try:
            final = urlsplit(fetch_live(f"{self.url}/{route}", self.host).url).path.strip("/")
        except DocsFetchError as e:
            if e.status not in MOVED_STATUSES:
                raise
            final = route
        if final == route or not self._is_visible(final):
            raise frappe.DoesNotExistError(_("Docs page not found"))
        return final

    def _to_hit(self, hit: dict) -> dict:
        return {
            "route": hit["route"],
            "title": escape_marked(hit["title"]),
            "excerpt": escape_marked(hit["content"]),
            "category_label": self._title_of(hit["route"]),
        }

    def _is_visible(self, route: str) -> bool:
        return (
            not _is_old_version(route)
            and (key := self._section_of(route)) is not None
            and key not in self.hidden
        )

    def _section_of(self, route: str) -> str | None:
        """The longest section key the route sits under."""
        keys = [k for k in self._all_sections() if route == k or route.startswith(f"{k}/")]
        return max(keys, key=len, default=None)

    def _title_of(self, route: str) -> str:
        return self._all_sections()[self._section_of(route)]

    def _all_sections(self) -> dict[str, str]:
        return self._cached("sections", SECTIONS_SECONDS, self._read_sections)

    def _read_sections(self) -> dict[str, str]:
        sections = {}
        for title, link in LLMS_LINK.findall(self._read_llms("llms.txt")):
            path = urlsplit(link).path
            if path.endswith("/llms.txt"):
                sections[path.removesuffix("/llms.txt").strip("/")] = plain_title(title)
        return sections

    def _read_llms(self, path: str) -> str:
        return self._cached(
            f"llms:{path}",
            SECTIONS_SECONDS,
            lambda: fetch(f"{self.url}/{path}", self.host).text,
        )

    def _call(self, method: str, live: bool = False, **params) -> dict:
        get = fetch_live if live else fetch
        return get(f"{self.url}/{API}.{method}", self.host, params=params).json()["message"]

    def _cached(self, key: str, seconds: int, read):
        key = f"{CACHE}:{self.url}:{key}"
        if (value := frappe.cache.get_value(key)) is None:
            value = read()
            frappe.cache.set_value(key, value, expires_in_sec=seconds)
        return value


def _is_old_version(route: str) -> bool:
    return any(OLD_VERSION.fullmatch(part) for part in route.split("/"))
