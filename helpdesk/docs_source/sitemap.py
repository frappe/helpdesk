import re
import time
from html import unescape
from urllib.parse import urlsplit

import frappe
from bs4 import BeautifulSoup
from frappe import _

from helpdesk.docs_source.fetch import DocsFetchError, fetch, fetch_live
from helpdesk.docs_source.indexed import CACHE, GONE_STATUSES, PAGE_SECONDS, IndexedSource
from helpdesk.docs_source.text import clean_html, has_dot_segment, plain_title

MAX_PAGES = 1000
PAGE_DELAY = 0.5
SAMPLE_PAGES = 3
MIN_TEXT = 200
LOC = re.compile(r"<loc>\s*(.*?)\s*</loc>", re.S)
MAIN = ("main", "article", "[role=main]")
NOISE = "nav, aside, header, footer, script, style"


class SitemapSource(IndexedSource):
    """A docs site with only a sitemap.xml: indexed here, pages read as HTML."""

    def __init__(self, url: str) -> None:
        super().__init__(url)
        self.base_path = urlsplit(self.url).path.rstrip("/")

    def is_available(self) -> bool:
        try:
            urls = self._page_urls()[:SAMPLE_PAGES]
        except DocsFetchError:
            return False
        for url in urls:
            try:
                _, html = self.extract_main(fetch(url, self.host).text)
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
        if not pages:
            raise DocsFetchError("No readable pages in the sitemap")
        return self.host, pages

    def extract_main(self, html: str) -> tuple[str, str]:
        """The title and sanitized main content of a page; empty when it has none."""
        try:
            soup = BeautifulSoup(html or "", "html.parser")
            main = next((m for sel in MAIN if (m := soup.select_one(sel))), None)
            if main is None:
                return "", ""
            heading = main.find("h1") or soup.find("h1") or soup.find("title")
            title = plain_title(heading.get_text()) if heading else ""
            if heading is not None and heading.name == "h1":
                heading.decompose()
            for tag in main.select(NOISE):
                tag.decompose()
            return title, clean_html(str(main))
        except Exception:
            return "", ""

    def _read_html(self, page: dict) -> str:
        key = f"{CACHE}:{page['url']}"
        if (html := frappe.cache.get_value(key)) is None:
            try:
                text = fetch_live(page["url"], self.host).text
            except DocsFetchError as e:
                if e.status in GONE_STATUSES:
                    raise frappe.DoesNotExistError(_("Docs page not found")) from None
                raise
            html = self.extract_main(text)[1]
            if not _text(html):
                raise frappe.DoesNotExistError(_("Docs page not found"))
            frappe.cache.set_value(key, html, expires_in_sec=PAGE_SECONDS)
        return html

    def _read_page(self, url: str) -> dict | None:
        try:
            title, html = self.extract_main(fetch(url, self.host).text)
        except DocsFetchError:
            return None  # ponytail: one bad page never fails the sync
        body = _text(html)
        route = urlsplit(url).path.strip("/")
        if not body or not title:
            return None
        return {"route": route, "title": title, "url": url, "body": body}

    def _page_urls(self) -> list[str]:
        """In-scope page URLs from /sitemap.xml, following a sitemap index one level."""
        text = fetch(f"https://{self.host}/sitemap.xml", self.host).text
        locs = [unescape(loc) for loc in LOC.findall(text)]
        if "<sitemapindex" in text:
            children, locs = locs, []
            for child in children:
                if not self._is_ours(child):
                    continue
                try:
                    locs += [unescape(loc) for loc in LOC.findall(fetch(child, self.host).text)]
                except DocsFetchError:
                    continue
                if len(locs) > MAX_PAGES * 2:
                    break
        urls = {}
        for loc in locs:
            if self._in_scope(loc):
                urls.setdefault(loc, None)
            if len(urls) > MAX_PAGES:
                break
        return list(urls)

    def _in_scope(self, loc: str) -> bool:
        parts = self._split(loc)
        if parts is None:
            return False
        route = parts.path.strip("/")
        in_path = parts.path == self.base_path or parts.path.startswith(f"{self.base_path}/")
        return in_path and bool(route) and not has_dot_segment(route)

    def _is_ours(self, loc: str) -> bool:
        parts = self._split(loc)
        return parts is not None and parts.hostname == self.host

    def _split(self, loc: str):
        try:
            parts = urlsplit(loc)
            return parts if parts.hostname == self.host else None
        except ValueError:
            return None


def _text(html: str) -> str:
    return " ".join(BeautifulSoup(html, "html.parser").get_text(" ").split())
