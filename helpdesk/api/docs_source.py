import json
from urllib.parse import urlsplit

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import cint

from helpdesk.api.article import get_related
from helpdesk.api.knowledge_base import SEARCH_QUERY_LENGTH, validate_public_access
from helpdesk.docs_source import get_source
from helpdesk.docs_source.fetch import DOWN_KEY, DocsFetchError, log_failure
from helpdesk.docs_source.index import DocsIndex
from helpdesk.docs_source.indexed import IndexedSource
from helpdesk.docs_source.llms import LlmsSource
from helpdesk.docs_source.sitemap import SitemapSource
from helpdesk.docs_source.sync import enqueue_sync, is_syncing
from helpdesk.docs_source.text import plain_title
from helpdesk.docs_source.wiki import WikiSource

WIKI = "Frappe Wiki"
SEARCH_LIMIT = 4
RELATED_DOCS_LIMIT = 6
CLEARED = {
    "docs_source_url": "",
    "docs_source_type": "",
    "docs_source_label": "",
    "docs_source_hidden_sections": "",
    "docs_source_synced_on": None,
    "docs_source_page_count": 0,
    "docs_source_truncated": 0,
    "docs_source_sync_error": "",
}


@frappe.whitelist(methods=["GET"])
def get_docs_source() -> dict | None:
    """The connected Docs source with its sync state, or None. Needs read on HD Settings.
    A failed live read of the sections gives `sections: []` and `sections_error: true`."""
    frappe.has_permission("HD Settings", "read", throw=True)
    settings = frappe.get_cached_doc("HD Settings")
    source = get_source()
    if not source:
        return None
    hidden = json.loads(settings.docs_source_hidden_sections or "[]")
    sections, sections_error = [], False
    try:
        sections = [{**s, "hidden": s["key"] in hidden} for s in source.sections()]
    except DocsFetchError:
        sections_error = True
    return {
        "url": settings.docs_source_url,
        "type": settings.docs_source_type,
        "label": settings.docs_source_label,
        "sections": sections,
        "sections_error": sections_error,
        "page_count": settings.docs_source_page_count,
        "synced_on": settings.docs_source_synced_on,
        "truncated": bool(settings.docs_source_truncated),
        "error": settings.docs_source_sync_error,
        "syncing": isinstance(source, IndexedSource) and is_syncing(),
    }


@frappe.whitelist(methods=["POST"])
def connect_docs_source(url: str) -> dict:
    """Connect one docs site: tries Frappe Wiki, then llms.txt, then a sitemap.
    Needs write on HD Settings. Indexed types start their first sync."""
    frappe.has_permission("HD Settings", "write", throw=True)
    if frappe.db.get_single_value("HD Settings", "docs_source_url", cache=False):
        frappe.throw(_("Disconnect the current docs source first."))
    url = _normalize_url(url)
    source_type, label = _detect(url)
    _save(
        {
            **CLEARED,
            "docs_source_url": url,
            "docs_source_type": source_type,
            "docs_source_label": label,
        }
    )
    frappe.cache.delete_value(DOWN_KEY)
    if source_type != WIKI:
        enqueue_sync()
    return get_docs_source()


@frappe.whitelist(methods=["POST"])
def disconnect_docs_source() -> None:
    """Forget the Docs source and delete its index. Converted Articles stay."""
    frappe.has_permission("HD Settings", "write", throw=True)
    _save(CLEARED)
    frappe.cache.delete_value(DOWN_KEY)
    DocsIndex().clear()


@frappe.whitelist(methods=["POST"])
def resync_docs_source() -> None:
    """Read an indexed site again. Refused for Frappe Wiki and with no source."""
    frappe.has_permission("HD Settings", "write", throw=True)
    if not isinstance(get_source(), IndexedSource):
        frappe.throw(_("This docs source has nothing to resync."))
    enqueue_sync()


@frappe.whitelist(methods=["POST"])
def set_hidden_sections(sections: list[str]) -> None:
    """Hide these sections of a Frappe Wiki. Each must be a key of its section list."""
    frappe.has_permission("HD Settings", "write", throw=True)
    source = get_source()
    if not isinstance(source, WikiSource):
        frappe.throw(_("Only a Frappe Wiki has sections."))
    try:
        keys = {s["key"] for s in source.sections()}
    except DocsFetchError:
        frappe.throw(_("The sections could not be read right now."))
    if unknown := [s for s in sections if s not in keys]:
        frappe.throw(_("Unknown sections: {0}").format(", ".join(unknown)))
    _save({"docs_source_hidden_sections": json.dumps(list(dict.fromkeys(sections)))})


@frappe.whitelist(allow_guest=True, methods=["GET"])  # nosemgrep
@rate_limit(limit=120, seconds=60, user_based=True)
def search_docs(query: str, limit: int = SEARCH_LIMIT) -> list[dict]:
    """Up to 4 Docs hits for `query`, as route, title and excerpt with matches in <mark>
    tags, and category_label. Empty with no source or when it is down. Guests only when
    the knowledge base is public."""
    validate_public_access()
    query = query.strip()[:SEARCH_QUERY_LENGTH]
    source = get_source()
    if not query or not source:
        return []
    try:
        hits = source.search(query)
    except DocsFetchError as e:
        log_failure(e)
        return []
    limit = cint(limit)
    return hits[: limit if 0 < limit <= SEARCH_LIMIT else SEARCH_LIMIT]


@frappe.whitelist(allow_guest=True, methods=["GET"])  # nosemgrep
@rate_limit(limit=120, seconds=60, user_based=True)
def get_doc_page(route: str) -> dict:
    """A Docs page plus `related: {docs, articles}`. Raises DoesNotExistError for a
    missing or hidden page, no source, or a source that is down."""
    validate_public_access()
    source = get_source()
    if not source:
        frappe.throw(_("Docs page not found"), frappe.DoesNotExistError)
    try:
        page = source.get_page(route)
    except DocsFetchError as e:
        log_failure(e)
        frappe.throw(_("Docs page not found"), frappe.DoesNotExistError)
    page["related"] = _related(source, page["route"], page["title"])
    return page


def _normalize_url(url: str) -> str:
    url = (url or "").strip().rstrip("/")
    message = _("Enter an https URL with a host and no user or password.")
    try:
        parts = urlsplit(url)
        host = parts.hostname
    except ValueError:
        frappe.throw(message)
    if parts.scheme != "https" or not host or "@" in parts.netloc:
        frappe.throw(message)
    if parts.query or parts.fragment or "?" in url or "#" in url:
        frappe.throw(_("The URL must not have a query or a fragment."))
    return url


def _detect(url: str) -> tuple[str, str]:
    if WikiSource(url, []).is_available():
        return WIKI, WIKI
    host = urlsplit(url).hostname
    if LlmsSource(url).is_available():
        return "llms.txt", host
    if SitemapSource(url).is_available():
        return "Sitemap", host
    frappe.throw(_("This site has no Frappe Wiki, llms.txt or sitemap we can read."))


def _save(values: dict) -> None:
    # Clears the cached doc now, and again after commit.
    frappe.db.set_single_value("HD Settings", values)


def _related(source, route: str, title: str) -> dict:
    articles = _related_articles(title)
    return {"docs": _related_docs(source, route, title, articles), "articles": articles}


def _related_articles(title: str) -> list[dict]:
    try:
        return get_related(title)
    except Exception:
        frappe.log_error("Docs page: related articles failed")
        return []


def _related_docs(source, route: str, title: str, articles: list[dict]) -> list[dict]:
    section = route.partition("/")[0]
    try:
        hits = source.search(title)
    except DocsFetchError as e:
        log_failure(e)
        return []
    except Exception:
        frappe.log_error("Docs page: related docs failed")
        return []
    article_titles, converted_routes = _article_matches(articles)
    docs, seen = [], set()
    for hit in hits:
        hit_title = plain_title(hit["title"]).casefold()
        if (
            hit["route"] == route
            or hit["route"] in converted_routes
            or hit["route"].partition("/")[0] != section
            or hit_title in seen
            or hit_title in article_titles
        ):
            continue
        seen.add(hit_title)
        docs.append({"route": hit["route"], "title": plain_title(hit["title"])})
    return docs[:RELATED_DOCS_LIMIT]


def _article_matches(articles: list[dict]) -> tuple[set[str], set[str]]:
    """Casefolded titles of Related Articles that are not Converted, and the Docs routes of those that are."""
    rows = frappe.get_all(
        "HD Article",
        filters={"name": ["in", [a["name"] for a in articles]]},
        fields=["name", "docs_page_route"],
    )
    converted = {r.name: r.docs_page_route for r in rows if r.docs_page_route}
    titles = {plain_title(a["title"]).casefold() for a in articles if a["name"] not in converted}
    return titles, set(converted.values())
