"""Where in the portal a customer started when they raised a ticket.

The portal's new-ticket page sends the `?from=` query of the link that led there.
Only the server turns it into field values, since the query is whatever the browser says.
"""

import frappe

ORIGIN_FIELDS = ("entry_point", "source_article", "source_search")

ENTRY_POINTS = {
    "article": "Article",
    "search": "Search",
    "ticket-list": "Ticket List",
    "closed-ticket": "Closed Ticket",
}
DIRECT = "Direct"
SEARCH_LENGTH = 140


def resolve_origin(origin: dict) -> dict:
    """Field values for a portal ticket; a bad origin degrades to Direct, never an error."""
    origin = origin if isinstance(origin, dict) else {}
    # str() so an unhashable value from the request falls through to Direct
    entry_point = ENTRY_POINTS.get(str(origin.get("from")), DIRECT)
    values = {"entry_point": entry_point}
    if entry_point == "Article":
        values["source_article"] = _readable_article(origin.get("article"))
    if entry_point == "Search":
        values["source_search"] = _search_text(origin.get("q"))
    return values


def _readable_article(article) -> str | None:
    # has_permission raises on a missing name, so existence is checked first
    if not isinstance(article, str) or not frappe.db.exists("HD Article", article):
        return None
    return article if frappe.has_permission("HD Article", "read", doc=article) else None


def _search_text(query) -> str | None:
    if not isinstance(query, str):
        return None
    return query.strip()[:SEARCH_LENGTH] or None
