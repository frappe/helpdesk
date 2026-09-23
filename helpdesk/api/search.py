# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

import json

import frappe
from frappe import _


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

    from frappe.search.sqlite_search import SQLiteSearchIndexMissingError

    from helpdesk.search_sqlite import HelpdeskSearch

    search = HelpdeskSearch()

    try:
        result = search.search(query, filters=_filters, title_only=title_only)
        return result
    except SQLiteSearchIndexMissingError:
        if "System Manager" in frappe.get_roles():
            frappe.throw(
                _(
                    "Search index not available. Build it by running helpdesk.search_sqlite.build_index."
                )
            )
        frappe.throw(_("Search is temporarily unavailable. Please try again later."))


@frappe.whitelist()
def get_filter_options():
    """Get available filter options for search interface"""
    from helpdesk.search_sqlite import HelpdeskSearch

    search = HelpdeskSearch()

    if not search.index_exists():
        return {
            "teams": {},
            "statuses": {},
            "priorities": {},
            "customers": {},
            "doctypes": {},
        }

    return search.get_filter_options()
