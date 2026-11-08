import frappe
from frappe import _
from frappe.utils.background_jobs import is_job_enqueued

from helpdesk.api.knowledge_base import _validate_category
from helpdesk.docs_source.importer import (
    JOB_ID,
    RESULT_KEY,
    RUNNING_SECONDS,
    DocsImportError,
    normalize_url,
    run_import,
)
from helpdesk.utils import agent_manager_only


@frappe.whitelist(methods=["POST"])
@agent_manager_only
def import_docs(url: str, category: str) -> dict:
    """Start copying up to 50 new pages of a docs site into `category` as Draft
    Articles, in a background job. Returns the state `get_import_result` gives; a
    bad address or a run already going comes back as an `error` state."""
    frappe.has_permission("HD Article", "create", throw=True)
    _validate_category(category)
    try:
        url = normalize_url(url)
    except DocsImportError as e:
        return {"state": "error", "message": str(e), "host": ""}
    host = url.split("/")[2]
    if is_job_enqueued(JOB_ID):
        message = _("An import is already running. It should finish in a few minutes.")
        return {"state": "error", "message": message, "host": host}
    started = {
        "state": "running",
        "stage": "waiting",
        "done": 0,
        "total": 0,
        "host": host,
    }
    frappe.cache.set_value(RESULT_KEY, started, expires_in_sec=RUNNING_SECONDS)
    frappe.enqueue(
        run_import,
        queue="long",
        timeout=900,
        job_id=JOB_ID,
        deduplicate=True,
        enqueue_after_commit=True,
        url=url,
        category=category,
    )
    return started


@frappe.whitelist(methods=["GET"])
@agent_manager_only
def get_import_result() -> dict | None:
    """The last import: `running` with its stage and progress, `done` with counts, or
    `error` with a plain message. None before any run."""
    result = frappe.cache.get_value(RESULT_KEY)
    if result and result["state"] == "running" and not is_job_enqueued(JOB_ID):
        message = _(
            "The import stopped before it finished. Try again. Pages already copied are kept."
        )
        return {"state": "error", "message": message, "host": result["host"]}
    return result
