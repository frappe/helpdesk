# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

import json

import frappe
from frappe import _


def _get_backend():
    """Return the configured ticket search backend (SQLite default, or RediSearch).

    Selected by ``HD Settings.search_backend``. Both backends expose the same
    public surface (``search``, ``get_filter_options``, ``index_exists``) and
    return the same shapes, so callers are backend-agnostic.
    """
    if frappe.db.get_single_value("HD Settings", "search_backend") == "RediSearch":
        from helpdesk.search_redisearch import HelpdeskRediSearch

        return HelpdeskRediSearch()

    from helpdesk.search_sqlite import HelpdeskSearch

    return HelpdeskSearch()


@frappe.whitelist()
def search(
    query: str, filters: str | None = None, limit: int = 20, title_only: bool = False
):
    """Main search endpoint for the dedicated search page"""
    # Input validation
    if not query or len(query.strip()) < 2:
        frappe.throw(_("Search query must be at least 2 characters"))

    # Validate and parse limit
    try:
        limit = min(int(limit or 20), 100)  # Max 100 results
    except (ValueError, TypeError):
        limit = 20

    # Parse filters safely
    _filters = {}
    if isinstance(filters, str):
        try:
            _filters = json.loads(filters) if filters else {}
        except json.JSONDecodeError:
            _filters = {}

    from helpdesk.search_sqlite import HelpdeskSearchIndexMissingError

    search = _get_backend()

    try:
        result = search.search(
            query, filters=_filters, title_only=title_only, limit=limit
        )
        return result
    except HelpdeskSearchIndexMissingError:
        frappe.throw(_("Search index not available. Please contact administrator."))


@frappe.whitelist()
def get_filter_options():
    """Get available filter options for search interface"""
    search = _get_backend()

    if not search.index_exists():
        return {
            "teams": {},
            "statuses": {},
            "priorities": {},
            "customers": {},
            "doctypes": {},
        }

    return search.get_filter_options()
