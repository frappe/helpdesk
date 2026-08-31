"""Shared helpers for the core-comments migration patches (not a patch)."""

from collections.abc import Iterator

import frappe

CHUNK_SIZE = 50_000


def iter_name_chunks(
    doctype: str, filters: dict | None = None
) -> Iterator[tuple[str, str]]:
    """Yield (lower, upper] name ranges covering `doctype` in CHUNK_SIZE steps.

    Name-ordered ranges keep each insert-select bounded; committing per chunk
    plus NOT EXISTS in the consumer makes an interrupted migrate resumable.
    """
    last = ""
    while True:
        names = frappe.get_all(
            doctype,
            filters={**(filters or {}), "name": [">", last]},
            order_by="name asc",
            limit_page_length=CHUNK_SIZE,
            pluck="name",
        )
        if not names:
            return
        yield last, names[-1]
        last = names[-1]
