import hashlib

import frappe
from frappe.utils import now
from frappe.utils.background_jobs import is_job_enqueued

from helpdesk.docs_source import get_source
from helpdesk.docs_source.index import (
    DocsIndex,
    is_no_redisearch,
    no_redisearch_message,
)
from helpdesk.docs_source.indexed import IndexedSource

JOB_PREFIX = "docs_source_sync"
REBUILD_KEY = "docs_source_rebuild_tried"
REBUILD_WAIT = 3600
JOB_TIMEOUT = 1800


def enqueue_sync() -> None:
    url = _read_url()
    frappe.enqueue(
        "helpdesk.docs_source.sync.run_sync",
        queue="long",
        timeout=JOB_TIMEOUT,
        job_id=job_id(url),
        deduplicate=True,
        enqueue_after_commit=True,
        url=url,
    )


def run_sync(url: str) -> None:
    """Read the site, then swap the index. Nothing changes when the read fails."""
    source = get_source() if _current_url() == url else None
    if not isinstance(source, IndexedSource):
        return
    try:
        label, pages = source.read_pages()
        if _current_url() != url:
            return
        DocsIndex().replace(pages, label)
    except Exception as e:
        _save({"docs_source_sync_error": _error_message(e)})
    else:
        _save(
            {
                "docs_source_label": label,
                "docs_source_synced_on": now(),
                "docs_source_page_count": len(pages),
                "docs_source_truncated": int(source.truncated),
                "docs_source_sync_error": "",
            }
        )


def rebuild_if_missing() -> None:
    """Scheduler hook: rebuild a lost index, at most once an hour. Never refreshes a healthy one."""
    index = DocsIndex()
    if (
        not isinstance(get_source(), IndexedSource)
        or not index.has_redisearch()
        or index.index_exists()
        or is_syncing()
    ):
        return
    if frappe.cache.get_value(REBUILD_KEY):
        return
    frappe.cache.set_value(REBUILD_KEY, 1, expires_in_sec=REBUILD_WAIT)
    enqueue_sync()


def is_syncing() -> bool:
    return is_job_enqueued(job_id(_read_url()))


def job_id(url: str) -> str:
    """One job per site URL, so a new site's sync is not dropped by an old one's."""
    return f"{JOB_PREFIX}_{hashlib.sha1((url or '').encode()).hexdigest()[:10]}"


def _read_url() -> str | None:
    """Plain read, safe in a web request: no lock, no commit."""
    return frappe.db.get_single_value("HD Settings", "docs_source_url", cache=False)


def _current_url() -> str | None:
    """For run_sync only: it commits."""
    # Locking read: a cached or snapshot read would miss a URL changed during the sync.
    url = frappe.db.get_single_value("HD Settings", "docs_source_url", for_update=True)
    frappe.db.commit()  # release the lock
    return url


def _error_message(e: Exception) -> str:
    if is_no_redisearch(e):
        return no_redisearch_message()
    frappe.log_error("Docs source sync failed")
    return str(e)[:140] or type(e).__name__


def _save(values: dict) -> None:
    frappe.db.set_single_value("HD Settings", values)
    frappe.db.commit()
