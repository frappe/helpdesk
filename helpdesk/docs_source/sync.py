import frappe
from frappe import _
from frappe.utils import now
from frappe.utils.background_jobs import is_job_enqueued
from redis.exceptions import ResponseError

from helpdesk.docs_source import get_source
from helpdesk.docs_source.index import DocsIndex
from helpdesk.docs_source.indexed import IndexedSource

JOB_ID = "docs_source_sync"
REBUILD_KEY = "docs_source_rebuild_tried"
REBUILD_WAIT = 3600
SYNC_TIMEOUT = 1800


def enqueue_sync() -> None:
    frappe.enqueue(
        "helpdesk.docs_source.sync.run_sync",
        queue="long",
        timeout=SYNC_TIMEOUT,
        job_id=JOB_ID,
        deduplicate=True,
        url=frappe.db.get_single_value("HD Settings", "docs_source_url"),
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
    except ResponseError:
        _save(
            {
                "docs_source_sync_error": _(
                    "Redis has no RediSearch module, so docs cannot be indexed."
                )
            }
        )
    except Exception as e:
        frappe.log_error("Docs source sync failed")
        _save({"docs_source_sync_error": str(e)[:140] or type(e).__name__})
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
    if not isinstance(get_source(), IndexedSource) or DocsIndex().index_exists() or is_syncing():
        return
    if frappe.cache.get_value(REBUILD_KEY):
        return
    frappe.cache.set_value(REBUILD_KEY, 1, expires_in_sec=REBUILD_WAIT)
    enqueue_sync()


def is_syncing() -> bool:
    return is_job_enqueued(JOB_ID)


def _current_url() -> str | None:
    return frappe.db.get_single_value("HD Settings", "docs_source_url")


def _save(values: dict) -> None:
    frappe.db.set_single_value("HD Settings", values)
    frappe.db.commit()
