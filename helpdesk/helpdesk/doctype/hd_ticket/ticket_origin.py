"""The portal's `?from=` query is untrusted, so only the server maps it to fields."""

import frappe

TICKET_ORIGIN_FIELDS = ("entry_point", "source_article", "source_search")

ENTRY_POINTS = {
    "article": "Article",
    "search": "Search",
    "ticket-list": "Ticket List",
    "closed-ticket": "Closed Ticket",
}
DIRECT = "Direct"
SEARCH_LENGTH = 140


def resolve_ticket_origin(origin: dict) -> dict:
    """A bad origin degrades to Direct, never an error."""
    origin = origin if isinstance(origin, dict) else {}
    # str(): unhashable request values fall through to Direct
    entry_point = ENTRY_POINTS.get(str(origin.get("from")), DIRECT)
    values = {"entry_point": entry_point}
    if entry_point == "Article":
        values["source_article"] = _accessible_article(origin.get("article"))
    if entry_point == "Search":
        values["source_search"] = _search_text(origin.get("q"))
    return values


def _accessible_article(article) -> str | None:
    # has_permission raises on a missing name
    if not isinstance(article, str) or not frappe.db.exists("HD Article", article):
        return None
    return article if frappe.has_permission("HD Article", "read", doc=article) else None


def _search_text(query) -> str | None:
    if not isinstance(query, str):
        return None
    return query.strip()[:SEARCH_LENGTH] or None
