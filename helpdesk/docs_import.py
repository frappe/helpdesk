from urllib.parse import urlsplit

import frappe
from frappe import _
from frappe.utils import add_to_date, now, now_datetime, sha256_hash
from frappe.web_crawler import CrawledPage, start_crawl
from frappe.web_crawler.limits import CrawlLimits
from frappe.website.doctype.web_crawl.web_crawl import ERRORS, STOPPED_REASONS

# Pages read per run, unless Web Crawl Settings allow fewer; importing again picks up the next batch.
MAX_PAGES = 200
TITLE_LENGTH = 140
URL_LENGTH = 500
ON_PAGE = "helpdesk.docs_import.import_page"
SKIP_URLS = "helpdesk.docs_import.skip_imported"
ERROR_CODES = {label: code for code, label in ERRORS.items()}


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


def page_limit() -> int:
    """The most pages one import reads: MAX_PAGES, or the lower Web Crawl Settings cap."""
    return min(MAX_PAGES, CrawlLimits.from_settings().max_pages)


def start_import(url: str, category: str):
    """Crawls the site's llms.txt and sitemap pages into `category` as Draft Articles."""
    return start_crawl(
        url,
        sitemap="only",
        limit=page_limit(),
        on_page=ON_PAGE,
        skip_urls=SKIP_URLS,
        reference_doctype="HD Article Category",
        reference_name=category,
    )


def skip_imported(urls: list[str]) -> list[str]:
    """Pages already imported, repeated in the list, or too long to store."""
    keys = {url: page_key(url) for url in urls}
    imported = set(
        frappe.get_all(
            "HD Article",
            {"docs_page_url": ("in", list(set(keys.values())))},
            pluck="docs_page_url",
        )
    )
    seen = set()
    skipped = []
    for url, key in keys.items():
        if len(key) > URL_LENGTH or key in imported or key in seen:
            skipped.append(url)
        seen.add(key)
    return skipped


def import_page(page: CrawledPage, web_crawl) -> None:
    """The crawl's `on_page`: copies a readable page as a Draft Article."""
    if not (page.ok and page.title):
        return
    article = frappe.get_doc(
        {
            "doctype": "HD Article",
            "title": page.title[:TITLE_LENGTH],
            "category": web_crawl.reference_name,
            "content": page.html,
            "status": "Draft",
            "docs_page_url": page_key(page.final_url or page.url),
            "docs_copied_on": now(),
        }
    ).insert()
    article.db_set("docs_content_hash", sha256_hash(article.content or ""))


def last_import() -> dict | None:
    """The last import: `running` with its stage and pages read, `done` with counts, or
    `error` with a plain message. None before any run."""
    crawl = frappe.db.get_value(
        "Web Crawl",
        {"on_page_method": ON_PAGE},
        [
            "name",
            "url",
            "status",
            "stopped_reason",
            "pages_crawled",
            "reference_name",
            "creation",
        ],
        order_by="creation desc",
        as_dict=True,
    )
    return crawl and ImportResult(crawl).as_dict()


class ImportResult:
    """The state of one import's Web Crawl, as the settings page shows it."""

    def __init__(self, crawl):
        self.crawl = crawl
        self.host = urlsplit(crawl.url).hostname

    def as_dict(self) -> dict:
        if self.crawl.status in ("Queued", "Running"):
            return self.running() if not self.stalled() else self.error(self.stopped())
        if self.crawl.status != "Completed":
            return self.error(self.stopped())
        created, skipped = self.created(), self.skipped()
        if not created and not skipped:
            return self.error(self.nothing_read())
        unreadable = self.unreadable()
        return {
            "state": "done",
            "created": created,
            "skipped": skipped,
            "failed": len(unreadable),
            "unreadable": unreadable,
            "host": self.host,
            "category": self.crawl.reference_name,
        }

    def running(self) -> dict:
        stage = "waiting" if self.crawl.status == "Queued" else "reading"
        if stage == "reading" and not self.crawl.pages_crawled:
            stage = "finding"
        return {
            "state": "running",
            "stage": stage,
            "done": self.crawl.pages_crawled,
            "host": self.host,
        }

    def stalled(self) -> bool:
        """Its job has run out of time, so a dead worker left it running."""
        timeout = CrawlLimits.from_settings().job_timeout()
        return self.crawl.creation < add_to_date(now_datetime(), seconds=-timeout)

    def created(self) -> int:
        keys = [page_key(url) for url in self.result_urls()]
        if not keys:
            return 0
        filters = {
            "docs_page_url": ("in", keys),
            "creation": (">=", self.crawl.creation),
        }
        return frappe.db.count("HD Article", filters)

    def skipped(self) -> int:
        """Pages of the site imported by earlier runs."""
        filters = {
            "docs_page_url": ("like", f"https://{self.host}%"),
            "creation": ("<", self.crawl.creation),
        }
        return frappe.db.count("HD Article", filters)

    def result_urls(self) -> list[str]:
        results = frappe.get_all(
            "Web Crawl Result",
            {"web_crawl": self.crawl.name, "error": ("is", "not set")},
            ["url", "final_url"],
        )
        return [result.final_url or result.url for result in results]

    def unreadable(self) -> list[dict]:
        results = frappe.get_all(
            "Web Crawl Result",
            {"web_crawl": self.crawl.name, "error": ("is", "set")},
            ["url", "error"],
            order_by="creation",
        )
        return [
            {"url": result.url, "reason": ERROR_CODES.get(result.error, "failed")}
            for result in results
        ]

    def error(self, message: str) -> dict:
        return {"state": "error", "message": message, "host": self.host}

    def stopped(self) -> str:
        return _(
            "The import stopped before it finished. Try again. Pages already copied are kept."
        )

    def nothing_read(self) -> str:
        if self.crawl.stopped_reason == STOPPED_REASONS["robots_too_large"]:
            return _(
                "The robots.txt of {0} is larger than Web Crawl Settings allow, so no page was read. Ask an administrator to raise Maximum robots.txt size."
            ).format(self.host)
        if self.crawl.pages_crawled:
            return _("We found pages on {0} but could not read any of them.").format(
                self.host
            )
        return _(
            "We couldn't find an llms.txt or sitemap.xml on {0}. Check the address, or try the root of the docs site."
        ).format(self.host)
