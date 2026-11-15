from urllib.parse import urlsplit

import frappe
from frappe import _
from frappe.utils.safe_exec import BlockedRequest

from helpdesk.api.knowledge_base import _validate_category, insert_category
from helpdesk.docs_import import (
    DocsImportError,
    last_import,
    normalize_url,
    page_limit,
    start_import,
)
from helpdesk.utils import agent_manager_only


@frappe.whitelist(methods=["POST"])
@agent_manager_only
def import_docs(
    url: str, category: str | None = None, new_category: str | None = None
) -> dict:
    """Start copying up to `get_page_limit()` new pages of a docs site into `category` as Draft
    Articles, in a background job. With `new_category`, a category of that name is
    created for them instead. Returns the state `get_import_result` gives; a bad
    address or a run already going comes back as an `error` state."""
    frappe.has_permission("HD Article", "create", throw=True)
    if not new_category:
        _validate_category(category)
    try:
        url = normalize_url(url)
    except DocsImportError as e:
        return {"state": "error", "message": str(e), "host": ""}
    host = urlsplit(url).hostname
    if (last_import() or {}).get("state") == "running":
        message = _("An import is already running. It should finish in a few minutes.")
        return {"state": "error", "message": message, "host": host}
    # Rolled back with a refused address, so a refusal leaves no empty category.
    frappe.db.savepoint("docs_import")
    try:
        if new_category:
            category = insert_category(new_category).name
        start_import(url, category)
    except BlockedRequest:
        frappe.db.rollback(save_point="docs_import")
        frappe.clear_messages()
        message = _(
            "We can't reach that address. Use the public address of your docs site."
        )
        return {"state": "error", "message": message, "host": host}
    return last_import()


@frappe.whitelist(methods=["GET"])
@agent_manager_only
def get_import_result() -> dict | None:
    """The last import: `running` with its stage and pages read, `done` with counts, or
    `error` with a plain message. None before any run."""
    return last_import()


@frappe.whitelist(methods=["GET"])
@agent_manager_only
def get_page_limit() -> int:
    """The most new pages one import reads, after the Web Crawl Settings cap."""
    return page_limit()
