"""Relabel HD Ticket Comment rows in the SQLite search index to Comment.

The comment migration preserved names, content and reference_ticket, so the
indexed rows stay valid; only the doctype label and doc_id prefix are stale.
An in-place UPDATE avoids rebuilding the whole index (hours on large sites,
with search down throughout). If the surgery fails, drop the index and let
core's after_migrate build_index_in_background do a full rebuild.
"""

import frappe

from helpdesk.search_sqlite import HelpdeskSearch

OLD_PREFIX_LENGTH = len("HD Ticket Comment:")


def execute():
    search = HelpdeskSearch()
    if not search.index_exists():
        return
    try:
        search.sql(
            """UPDATE search_fts
            SET doc_id = 'Comment:' || substr(doc_id, ?),
                doctype = 'Comment',
                reference_doctype = 'HD Ticket',
                reference_name = CAST(reference_ticket AS TEXT),
                reference_ticket = CAST(reference_ticket AS TEXT)
            WHERE doctype = 'HD Ticket Comment'""",
            (OLD_PREFIX_LENGTH + 1,),
            commit=True,
        )
        # rows indexed in the autoincrement-naming era store ticket names as
        # SQLite integers; the permission prefilter binds strings, and SQLite
        # compares strictly by type, so those rows never match
        search.sql(
            """UPDATE search_fts
            SET reference_ticket = CAST(reference_ticket AS TEXT),
                reference_name = CAST(reference_name AS TEXT)
            WHERE typeof(reference_ticket) = 'integer'
                OR typeof(reference_name) = 'integer'""",
            commit=True,
        )
    except Exception:  # noqa: BLE001 - any failure falls back to a full rebuild
        frappe.log_error(title="Comment search index relabel failed, rebuilding")
        search.drop_index()
