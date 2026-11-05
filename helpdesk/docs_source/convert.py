import frappe
from frappe import _
from frappe.utils import now
from frappe.website.utils import cleanup_page_name

from helpdesk.docs_source import get_source
from helpdesk.docs_source.fetch import DocsFetchError, log_failure
from helpdesk.docs_source.text import plain_title
from helpdesk.helpdesk.doctype.hd_article.hd_article import make_article_filters

MAX_BULK = 50
TITLE_LENGTH = 140
RESULT_SECONDS = 3600
SAVEPOINT = "docs_convert"


def convert_page(route: str, category: str) -> str:
    """Copy a Docs page into a new Draft Article in `category`. Returns the Article name."""
    from helpdesk.api.knowledge_base import _validate_category

    frappe.has_permission("HD Article", "create", throw=True)
    _validate_category(category)
    return _convert(route, category)


def converted_article(route: str) -> dict | None:
    """A Published Converted Article this reader can read, as name and title_slug."""
    rows = frappe.get_all(
        "HD Article",
        filters=make_article_filters(docs_page_route=route.strip("/")),
        fields=["name", "title"],
        limit=1,
    )
    return {"name": rows[0].name, "title_slug": cleanup_page_name(rows[0].title)} if rows else None


def readable_converted_routes(routes: list[str]) -> set[str]:
    """The routes among `routes` whose Converted Article this reader can read."""
    if not routes:
        return set()
    filters = make_article_filters(docs_page_route=["in", routes])
    return set(frappe.get_all("HD Article", filters=filters, pluck="docs_page_route"))


def mark_pages(pages: list[dict]) -> None:
    """For agents: add `converted` and `matching` ({name, title} or None) with 2 queries."""
    routes = [p["route"] for p in pages]
    converted = {
        r.docs_page_route: _ref(r)
        for r in frappe.get_all(
            "HD Article",
            filters={"docs_page_route": ["in", routes]},
            fields=["name", "title", "docs_page_route"],
        )
    }
    titles = {p["route"]: plain_title(p["title"])[:TITLE_LENGTH] for p in pages}
    matching = {}
    for r in frappe.get_all(
        "HD Article",
        filters={
            "title": ["in", list(set(titles.values()))],
            "docs_page_route": ["is", "not set"],
            "status": ["!=", "Archived"],
        },
        fields=["name", "title"],
        order_by="creation",
    ):
        matching.setdefault(r.title.casefold(), _ref(r))
    for page in pages:
        page["converted"] = converted.get(page["route"])
        page["matching"] = matching.get(titles[page["route"]].casefold())


def run_bulk(routes: list[str], category: str, user: str) -> None:
    """The background job: convert each page, skip failures, store the counts."""
    created = skipped = 0
    for route in routes:
        frappe.db.savepoint(SAVEPOINT)
        try:
            _convert(route, category)
            created += 1
        except Exception:
            frappe.db.rollback(save_point=SAVEPOINT)
            frappe.log_error(f"Docs bulk convert skipped {route}")
            skipped += 1
    frappe.db.commit()
    frappe.cache.set_value(
        result_key(user), {"created": created, "skipped": skipped}, expires_in_sec=RESULT_SECONDS
    )


def result_key(user: str) -> str:
    return f"docs_bulk_convert:{user}"


def _convert(route: str, category: str) -> str:
    source = get_source()
    if not source:
        frappe.throw(_("No docs source is connected."))
    try:
        page = source.get_page(route)
    except DocsFetchError as e:
        log_failure(e)
        frappe.throw(_("The docs page could not be read right now."))
    # ponytail: check-then-insert races, a unique index if concurrent converts matter
    if frappe.db.exists("HD Article", {"docs_page_route": page["route"]}):
        frappe.throw(_("This docs page is already converted."))
    return (
        frappe.get_doc(
            {
                "doctype": "HD Article",
                "title": plain_title(page["title"])[:TITLE_LENGTH],
                "category": category,
                "content": page["content"],
                "status": "Draft",
                "docs_page_route": page["route"],
                "docs_page_url": page["source_url"],
                "docs_copied_on": now(),
            }
        )
        .insert()
        .name
    )


def _ref(row) -> dict:
    return {"name": row.name, "title": row.title}
