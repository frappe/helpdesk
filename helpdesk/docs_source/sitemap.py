import re
import time
from collections.abc import Iterator
from html import unescape
from urllib.parse import urlsplit

import frappe
from bs4 import BeautifulSoup
from frappe import _

from helpdesk.docs_source.fetch import DocsFetchError, fetch
from helpdesk.docs_source.indexed import IndexedSource
from helpdesk.docs_source.text import clean_html, has_dot_segment, plain_title

MAX_PAGES = 1000
MAX_SITEMAPS = 50
PAGE_DELAY = 0.5
SAMPLE_PAGES = 3
MIN_TEXT = 200
LOC = re.compile(r"<loc>([^<]*)</loc>")
VERSION = re.compile(r"^(v?\d+(\.(\d+|x))*|next)$")
MAIN = ("article", "[role=main]", "main")
NOISE = "nav, header, footer, script, style, .theme-doc-toc-mobile, .theme-doc-version-badge"
PERMALINKS = "a.headerlink, a.hash-link"


class SitemapSource(IndexedSource):
    """A docs site with only a sitemap.xml: indexed here, pages read as HTML."""

    def __init__(self, url: str) -> None:
        super().__init__(url)
        self.base_path = urlsplit(self.url).path.rstrip("/")

    def is_available(self) -> bool:
        try:
            urls = next((chunk for chunk in self._sitemaps() if chunk), [])[:SAMPLE_PAGES]
        except DocsFetchError:
            return False
        for url in urls:
            try:
                html = self.extract_main(fetch(url, self.host).text)[1]
            except DocsFetchError:
                continue
            if len(_text(html)) >= MIN_TEXT:
                return True
        return False

    def read_pages(self) -> tuple[str, list[dict]]:
        urls = self._page_urls()
        self.truncated = len(urls) > MAX_PAGES
        urls = urls[:MAX_PAGES]
        pages = []
        for i, url in enumerate(urls):
            if page := self._read_page(url):
                pages.append(page)
            if i < len(urls) - 1:
                time.sleep(PAGE_DELAY)
        # A mostly failed read is an outage: keep the old index.
        if not pages or (len(urls) - len(pages)) * 2 > len(urls):
            raise DocsFetchError("Most pages in the sitemap could not be read")
        return self.host, pages

    def extract_main(self, html: str) -> tuple[str, str]:
        """The title and sanitized main content of a page; empty when it has none."""
        soup = BeautifulSoup(html or "", "html.parser")
        main = next((m for sel in MAIN if (m := soup.select_one(sel))), None)
        if main is None:
            return "", ""
        for tag in main.select(PERMALINKS):
            tag.decompose()
        # Starlight callouts are asides, so an article keeps them.
        noise = NOISE if main.name == "article" else f"{NOISE}, aside"
        for tag in main.select(noise):
            # Docusaurus puts the page h1 in a header.
            if tag.parent is not None and not (tag.name == "header" and tag.find("h1")):
                tag.decompose()
        heading = main.find("h1") or soup.find("title")
        title = plain_title(heading.get_text()) if heading else ""
        if heading is not None and heading.name == "h1":
            heading.decompose()
        return title, clean_html(str(main))

    def _to_html(self, text: str, page: dict) -> str:
        html = self.extract_main(text)[1]
        if not _text(html):
            raise frappe.DoesNotExistError(_("Docs page not found"))
        return html

    def _read_page(self, url: str) -> dict | None:
        try:
            title, html = self.extract_main(fetch(url, self.host).text)
        except DocsFetchError:
            return None  # ponytail: one bad page never fails the sync
        body = _text(html)
        if not body or not title:
            return None
        return {"route": urlsplit(url).path.strip("/"), "title": title, "url": url, "body": body}

    def _page_urls(self) -> list[str]:
        """In-scope page URLs, unversioned first so the cap cuts old versions."""
        routes = {}
        for chunk in self._sitemaps():
            for url in chunk:
                routes.setdefault(urlsplit(url).path.strip("/"), url)
        return sorted(routes.values(), key=lambda url: _is_versioned(urlsplit(url).path))

    def _sitemaps(self) -> Iterator[list[str]]:
        """In-scope URLs of each sitemap, following a sitemap index one level."""
        text = self._read_root()
        if "<sitemapindex" not in text:
            yield self._in_scope(_locs(text))
            return
        for child in [loc for loc in _locs(text) if self._split(loc)][:MAX_SITEMAPS]:
            try:
                yield self._in_scope(_locs(fetch(child, self.host).text))
            except DocsFetchError:
                continue

    def _read_root(self) -> str:
        error = None
        for url in dict.fromkeys([f"{self.url}/sitemap.xml", f"https://{self.host}/sitemap.xml"]):
            try:
                text = fetch(url, self.host).text
            except DocsFetchError as e:
                error = e
                continue
            if "<loc>" in text:
                return text
            error = DocsFetchError("No sitemap found")
        raise error

    def _in_scope(self, locs: list[str]) -> list[str]:
        urls = []
        for loc in locs:
            parts = self._split(loc)
            if parts is None:
                continue
            route = parts.path.strip("/")
            in_path = parts.path == self.base_path or parts.path.startswith(f"{self.base_path}/")
            if in_path and route and not has_dot_segment(route):
                urls.append(loc)
        return urls

    def _split(self, loc: str):
        """The parsed URL when it is on our host, else None."""
        try:
            parts = urlsplit(loc)
            return parts if parts.hostname == self.host else None
        except ValueError:
            return None


def _locs(text: str) -> list[str]:
    return [unescape(loc.strip()) for loc in LOC.findall(text)]


def _is_versioned(path: str) -> bool:
    return any(VERSION.match(part) for part in path.split("/"))


def _text(html: str) -> str:
    return " ".join(BeautifulSoup(html, "html.parser").get_text(" ").split())
