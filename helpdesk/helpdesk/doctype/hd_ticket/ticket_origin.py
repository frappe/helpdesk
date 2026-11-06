"""The portal's `?from=` and `?utm_source=` queries are untrusted, so only the server
maps them to fields."""

import frappe

TICKET_ORIGIN_FIELDS = ("entry_point", "source_article", "source_search", "utm_source")

ENTRY_POINTS = {
    "article": "Article",
    "search": "Search",
    "ticket-list": "Ticket List",
    "closed-ticket": "Closed Ticket",
}
DIRECT = "Direct"
# a link from another site, such as the Frappe Cloud dashboard
EXTERNAL = "External"
SEARCH_LENGTH = 140


def resolve_ticket_origin(origin: dict) -> dict:
    """A bad origin degrades to Direct, never an error."""
    origin = origin if isinstance(origin, dict) else {}
    # another site's tag wins over the portal's own `from`
    if utm_source := _short_text(origin.get("utm_source")):
        return {"entry_point": EXTERNAL, "utm_source": utm_source}
    # str(): unhashable request values fall through to Direct
    entry_point = ENTRY_POINTS.get(str(origin.get("from")), DIRECT)
    values = {"entry_point": entry_point}
    if entry_point == "Article":
        values["source_article"] = _accessible_article(origin.get("article"))
    if entry_point == "Search":
        values["source_search"] = _short_text(origin.get("q"))
    return values


def _accessible_article(article) -> str | None:
    # has_permission raises on a missing name
    if not isinstance(article, str) or not frappe.db.exists("HD Article", article):
        return None
    return article if frappe.has_permission("HD Article", "read", doc=article) else None


def _short_text(value) -> str | None:
    if not isinstance(value, str):
        return None
    return value.strip()[:SEARCH_LENGTH] or None
