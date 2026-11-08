import time
from urllib.parse import urlsplit

import frappe
from frappe import _
from frappe.utils import now

from helpdesk.api.knowledge_base import content_hash
from helpdesk.docs_source import llms, sitemap
from helpdesk.docs_source.fetch import MAX_CANDIDATES, DocsFetchError
from helpdesk.docs_source.text import absolute_links, plain_title, visible_text
from helpdesk.helpdesk.doctype.hd_article_category.hd_article_category import (
    batched_article_index,
)

MAX_PAGES = 50
PAGE_PAUSE = 0.5
TITLE_LENGTH = 140
URL_LENGTH = 500
GONE_STATUSES = (404, 410)
DENIED_STATUSES = (401, 403, 429)
JOB_ID = "docs_import"
RESULT_KEY = "docs_import_result"
RUNNING_SECONDS = 3600
RESULT_SECONDS = 7 * 24 * 3600


class DocsImportError(Exception):
    """What went wrong, worded for the person who pasted the address."""


def normalize_url(url: str) -> str:
    """The pasted address as `https://host[/path]`, or a DocsImportError."""
    bad = DocsImportError(
        _("Enter a public https:// address, like https://docs.example.com.")
    )
    if not isinstance(url, str) or len(url) > URL_LENGTH:
        raise bad
    url = url.strip()
    if "://" not in url:
        url = f"https://{url}"
    try:
        parts = urlsplit(url)
        host, _port = parts.hostname, parts.port
    except ValueError:
        raise bad from None
    if parts.scheme != "https" or not host or parts.username or parts.password:
        raise bad
    return f"https://{parts.netloc.lower()}{parts.path.rstrip('/')}"


def page_key(url: str) -> str:
    """The stored address of a page: no fragment, query, trailing slash or `.md`."""
    parts = urlsplit(url)
    path = parts.path.rstrip("/").removesuffix(".md")
    return f"https://{parts.netloc.lower()}{path}"


class DocsImport:
    """Copy up to MAX_PAGES new pages of a docs site into a category as Draft Articles."""

    def __init__(self, url: str, category: str):
        self.url = normalize_url(url)
        self.category = category
        self.host = urlsplit(self.url).hostname
        self.read_page = llms.read_page

    def run(self) -> dict:
        """Returns the number of pages `created`, `skipped` as already imported and `failed`."""
        self.report("finding")
        new, skipped = self.drop_imported(self.find_pages())
        batch = list(new.items())[:MAX_PAGES]
        created = failed = 0
        with batched_article_index():
            for done, (key, url) in enumerate(batch):
                self.report("reading", done, len(batch))
                if done:
                    time.sleep(PAGE_PAUSE)
                if self.import_page(key, url):
                    created += 1
                else:
                    failed += 1
        frappe.db.commit()  # sends the search index job
        if batch and not created:
            raise DocsImportError(
                _("We found pages on {0} but could not read any of them.").format(
                    self.host
                )
            )
        return {"created": created, "skipped": skipped, "failed": failed}

    def find_pages(self) -> list[str]:
        """Page URLs from llms.txt, else sitemap.xml. Sets the reader to match."""
        error = None
        for source in (llms, sitemap):
            try:
                urls = source.find_pages(self.url)
            except DocsFetchError as e:
                if e.status not in GONE_STATUSES:
                    error = error or e
                continue
            if urls:
                self.read_page = source.read_page
                return urls
        if error:
            raise DocsImportError(self.friendly(error))
        raise DocsImportError(
            _(
                "We couldn't find an llms.txt or sitemap.xml on {0}. Check the address, or try the root of the docs site."
            ).format(self.host)
        )

    def drop_imported(self, urls: list[str]) -> tuple[dict[str, str], int]:
        """The new pages as `{key: url}`, and how many were already imported."""
        pages = {}
        for url in urls:
            key = page_key(url)
            if len(key) <= URL_LENGTH:
                pages.setdefault(key, url)
        imported = set(
            frappe.get_list(
                "HD Article",
                filters={"docs_page_url": ["in", list(pages)]},
                pluck="docs_page_url",
                limit=MAX_CANDIDATES,
            )
        )
        return {k: u for k, u in pages.items() if k not in imported}, len(imported)

    def import_page(self, key: str, url: str) -> bool:
        """Copy one page. False when it can't be read or saved; the run goes on."""
        frappe.db.savepoint("docs_page")
        try:
            if page := self.read_one(url):
                self.insert_draft(key, url, *page)
                frappe.db.commit()  # keeps the pages already copied if the job is killed
                return True
        except DocsFetchError:
            pass
        except Exception:
            frappe.db.rollback(save_point="docs_page")
            frappe.log_error(f"Docs import failed: {key}")
        return False

    def read_one(self, url: str) -> tuple[str, str] | None:
        """The page's title and HTML, or None when it has no title or no text."""
        title, html = self.read_page(url)
        title = plain_title(title)[:TITLE_LENGTH]
        return (
            (title, absolute_links(html, url)) if title and visible_text(html) else None
        )

    def insert_draft(self, key: str, url: str, title: str, html: str) -> None:
        article = frappe.get_doc(
            {
                "doctype": "HD Article",
                "title": title,
                "category": self.category,
                "content": html,
                "status": "Draft",
                "docs_page_url": key,
                "docs_copied_on": now(),
            }
        ).insert()
        article.db_set("docs_content_hash", content_hash(article.content))

    def report(self, stage: str, done: int = 0, total: int = 0) -> None:
        """Progress for the settings page: a cache write, no database."""
        frappe.cache.set_value(
            RESULT_KEY,
            {
                "state": "running",
                "stage": stage,
                "done": done,
                "total": total,
                "host": self.host,
            },
            expires_in_sec=RUNNING_SECONDS,
        )

    def friendly(self, error: DocsFetchError) -> str:
        """Plain words for a failed fetch, never the error text."""
        if error.status in DENIED_STATUSES:
            return _(
                "{0} did not let us read its pages. Check that the site is public and allows crawlers."
            ).format(self.host)
        if error.transient or (error.status or 0) >= 500:
            return _("{0} did not answer in time. Try again in a few minutes.").format(
                self.host
            )
        if error.status:
            return _(
                "We couldn't find an llms.txt or sitemap.xml on {0}. Check the address, or try the root of the docs site."
            ).format(self.host)
        return _(
            "We can't reach that address. Use the public address of your docs site."
        )
